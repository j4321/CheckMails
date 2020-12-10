# -*- coding: utf-8 -*-
"""
CheckMails - System tray unread mail checker
Copyright 2016-2020 Juliette Monsel <j_4321@protonmail.com>

CheckMails is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CheckMails is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

IM_QUESTION_DATA and  IM_ERROR_DATA were taken from "icons.tcl":

    A set of stock icons for use in Tk dialogs. The icons used here
    were provided by the Tango Desktop project which provides a
    unified set of high quality icons licensed under the
    Creative Commons Attribution Share-Alike license
    (http://creativecommons.org/licenses/by-sa/3.0/)

    See http://tango.freedesktop.org/Tango_Desktop_Project

    Copyright (c) 2009 Pat Thoyts <patthoyts@users.sourceforge.net>

The other icons are modified versions of icons from the elementary project
Copyright 2007-2013 elementary LLC.


Constants
"""


from re import search
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
import os
from configparser import ConfigParser
from locale import getdefaultlocale
import gettext
from subprocess import check_output, CalledProcessError
import logging
from logging.handlers import TimedRotatingFileHandler
import warnings
from tkinter import TclVersion
from tkinter.messagebox import showwarning

# --- paths
PATH = os.path.dirname(__file__)

if os.access(PATH, os.W_OK) and os.path.exists(os.path.join(PATH, "images")):
    # the app is not installed
    # local directory containing config files
    LOCAL_PATH = os.path.join(PATH, "config")
    PATH_LOCALE = os.path.join(PATH, "locale")
    PATH_IMAGES = os.path.join(PATH, "images")
else:
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".checkmails")
    PATH_LOCALE = "/usr/share/locale"
    PATH_IMAGES = "/usr/share/checkmails/images"

if not os.path.isdir(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)
PATH_CONFIG = os.path.join(LOCAL_PATH, "checkmails.ini")
LOG_PATH = os.path.join(LOCAL_PATH, "checkmails.log")


# --- log
handler = TimedRotatingFileHandler(LOG_PATH, when='midnight',
                                   interval=1, backupCount=7)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)s: %(message)s',
                    handlers=[handler])
logging.getLogger().addHandler(logging.StreamHandler())


# --- ttf fonts
local_path = os.path.join(os.path.expanduser("~"), ".fonts")
try:
    local_fonts = os.listdir(local_path)
except FileNotFoundError:
    local_fonts = []
TTF_FONTS = {f.split(".")[0]: os.path.join(local_path, f)
             for f in local_fonts if search(r".(ttf|TTF)$", f)}
for root, dirs, files in os.walk("/usr/share/fonts"):
    for f in files:
        if search(r".(ttf|TTF)$", f):
            TTF_FONTS[f.split(".")[0]] = os.path.join(root, f)
if "LiberationSans-Bold" in TTF_FONTS:
    default_font = "LiberationSans-Bold"
elif TTF_FONTS:
    default_font = list(TTF_FONTS.keys())[0]
else:
    default_font = ""

# --- keyring
SERVICE_NAME = "CheckMails system tray unread mail checker"
USERNAME = os.getlogin()

try:
    import keyring
except ImportError:
    KEYRING = False
else:
    KEYRING = True


    def store_pwd_in_keyring(pwd):
        try:
            keyring.set_password(SERVICE_NAME, USERNAME, pwd)
        except keyring.errors.KeyringError:
            return


    def get_pwd_from_keyring():
        try:
            return keyring.get_password(SERVICE_NAME, USERNAME)
        except keyring.errors.KeyringError:
            return


# --- read config file
default_config = {
    "General": {
        "trayicon": "",
        "language": "",
        "font": default_font,
        "time": "300000",
        "timeout": "60000",
        "check_update": "True"
    },
    "Mailboxes": {
        "active": "",
        "inactive": ""
    }
}

CONFIG = ConfigParser()
for section, opts in default_config.items():
    CONFIG.setdefault(section, opts)
CONFIG.read(PATH_CONFIG)
LANGUE = CONFIG.get("General", "language")

if CONFIG.get("General", "font") not in TTF_FONTS:
    CONFIG.set("General", "font", default_font)


def save_config():
    """Save configuration to config file."""
    with open(PATH_CONFIG, 'w') as fichier:
        CONFIG.write(fichier)


# --- system tray icon
def get_available_gui_toolkits():
    """Check which gui toolkits are available to create a system tray icon."""
    toolkits = {'gtk': True, 'qt': True, 'tk': True}
    b = False
    try:
        import gi
        b = True
    except ImportError:
        toolkits['gtk'] = False

    try:
        import PyQt5
        b = True
    except ImportError:
        try:
            import PyQt4
            b = True
        except ImportError:
            try:
                import PySide
                b = True
            except ImportError:
                toolkits['qt'] = False

    tcl_packages = check_output(["tclsh",
                                 os.path.join(PATH, "packages.tcl")]).decode().strip().split()
    toolkits['tk'] = "tktray" in tcl_packages
    b = b or toolkits['tk']
    if not b:
        raise ImportError("No GUI toolkits available to create the system tray icon.")
    return toolkits


TOOLKITS = get_available_gui_toolkits()
GUI = CONFIG.get("General", "trayicon").lower()

if not TOOLKITS.get(GUI):
    DESKTOP = os.environ.get('XDG_CURRENT_DESKTOP')
    if DESKTOP == 'KDE':
        if TOOLKITS['qt']:
            GUI = 'qt'
        else:
            warnings.warn("No version of PyQt was found, falling back to another GUI toolkits so the system tray icon might not behave properly in KDE.")
            GUI = 'gtk' if TOOLKITS['gtk'] else 'tk'
    else:
        if TOOLKITS['gtk']:
            GUI = 'gtk'
        elif TOOLKITS['qt']:
            GUI = 'qt'
        else:
            GUI = 'tk'
    CONFIG.set("General", "trayicon", GUI)


# --- Translation
APP_NAME = "checkmails"

if LANGUE not in ["en", "fr"]:
    # Check the default locale
    lc = getdefaultlocale()[0][:2]
    if lc == "fr":
        # If we have a default, it's the first in the list
        LANGUE = "fr_FR"
    else:
        LANGUE = "en_US"
    CONFIG.set("General", "language", LANGUE[:2])

gettext.find(APP_NAME, PATH_LOCALE)
gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
gettext.bindtextdomain(APP_NAME, PATH_LOCALE)
gettext.textdomain(APP_NAME)
LANG = gettext.translation(APP_NAME, PATH_LOCALE,
                           languages=[LANGUE], fallback=True)
LANG.install()


# --- Cryptographic functions to safely store login information
def decrypt(mailbox, pwd):
    """Returns the login and password for the mailbox that where encrypted using pwd."""
    key = hashlib.sha256(pwd.encode()).digest()
    try:
        with open(os.path.join(LOCAL_PATH, mailbox), 'rb') as fich:
            iv = fich.read(AES.block_size)
            cipher = AES.new(key, AES.MODE_CFB, iv)
            server, login, password, folder = cipher.decrypt(fich.read()).decode().split("\n")
    except FileNotFoundError:
        showwarning(_("Warning"), _("Unknown mailbox %(name)r will be removed from configuration file.") % {'name': mailbox})
        active = CONFIG.get("Mailboxes", "active").split(", ")
        inactive = CONFIG.get("Mailboxes", "inactive").split(", ")
        while "" in active:
            active.remove("")
        while "" in inactive:
            inactive.remove("")
        if mailbox in active:
            active.remove(mailbox)
        if mailbox in inactive:
            inactive.remove(mailbox)
        CONFIG.set("Mailboxes", "active", ", ".join(active))
        CONFIG.set("Mailboxes", "inactive", ", ".join(inactive))
        save_config()
        return None, None, None, None
    return server, login, password, folder


def encrypt(mailbox, pwd, server, login, password, folder):
    """Encrypt the mailbox connection information using pwd."""
    key = hashlib.sha256(pwd.encode()).digest()
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CFB, iv)
    info = [server, login, password, folder]
    with open(os.path.join(LOCAL_PATH, mailbox), 'wb') as fich:
        fich.write(iv)
        try:
            fich.write(cipher.encrypt("\n".join(info)))
        except TypeError:
            fich.write(cipher.encrypt("\n".join(info).encode()))


# --- Images
ICON = os.path.join(LOCAL_PATH, "icon_mail.png")
if GUI == 'tk':
    IMAGE = os.path.join(PATH_IMAGES, "mail.png")
    FONTSIZE = 10
else:
    IMAGE = os.path.join(PATH_IMAGES, "mail128.png")
    FONTSIZE = 70
ICON_48 = os.path.join(PATH_IMAGES, "mail48.png")
IMAGE2 = os.path.join(PATH_IMAGES, "mail.svg")
ADD = os.path.join(PATH_IMAGES, "add.png")
DEL = os.path.join(PATH_IMAGES, "del.png")
EDIT = os.path.join(PATH_IMAGES, "edit.png")
IM_ERROR = os.path.join(PATH_IMAGES, "error.png")
IM_QUESTION = os.path.join(PATH_IMAGES, "question.png")


def internet_on():
    """Check the Internet connexion."""
    try:
        check_output(["ping", "-c", "1", "www.google.com"])
        return True
    except CalledProcessError:
        return False


# --- compatibility
if TclVersion < 8.6:
    # then tkinter cannot import PNG files directly, we need to use PIL
    # but to create an image from a string with the data keyword, we still need
    # the regular tkinter.PhotoImage
    from PIL import ImageTk
    from tkinter import PhotoImage as TkPhotoImage

    class MetaPhotoImage(type):
        def __call__(cls, *args, **kwargs):
            if 'file' in kwargs:
                return ImageTk.PhotoImage(*args, **kwargs)
            else:
                return TkPhotoImage(*args, **kwargs)

    class PhotoImage(metaclass=MetaPhotoImage):
        pass

else:
    # no need of ImageTk dependency
    from tkinter import PhotoImage
