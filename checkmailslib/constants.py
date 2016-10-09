#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checkmails - System tray unread mail checker
Copyright 2016 Juliette Monsel <j_4321@sfr.fr>

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

Constants
"""

import hashlib
from Crypto.Cipher import AES
from Crypto import Random
import os
from configparser import ConfigParser
from locale import getdefaultlocale
import gettext
from subprocess import check_output, CalledProcessError

VERSION = "1.0.0"

# path to application data (images,...)
PATH = os.path.dirname(__file__)

# path to configuration file and icon (needs to be writable)
LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".checkmails")
if not os.path.exists(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)

PATH_CONFIG = os.path.join(LOCAL_PATH, 'checkmails.ini')
PATH_LOCALE = os.path.join(PATH, "locale")


# read config file
CONFIG = ConfigParser()
if os.path.exists(PATH_CONFIG):
    CONFIG.read(PATH_CONFIG)
    LANGUE = CONFIG.get("General","language")
else:
    LANGUE = ""
    CONFIG.add_section("General")
    CONFIG.add_section("Mailboxes")
    # time in ms between to checks
    CONFIG.set("General", "time", "300000")
    CONFIG.set("General", "timeout", "60000")
    CONFIG.set("Mailboxes", "active", "")
    CONFIG.set("Mailboxes", "inactive", "")

def save_config():
    """ sauvegarde du dictionnaire contenant la configuration du logiciel (langue ...) """
    with open(PATH_CONFIG, 'w') as fichier:
        CONFIG.write(fichier)

# Translation

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

# Cryptographic functions to safely store login information
def decrypt(mailbox, pwd):
    """ Returns the login and password for the mailbox that where encrypted using pwd"""
    key = hashlib.sha256(pwd.encode()).digest()
    with open(os.path.join(LOCAL_PATH, mailbox), 'rb') as fich:
        iv = fich.read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        server, login, password, folder = cipher.decrypt(fich.read()).decode().split("\n")
    return server, login, password, folder

def encrypt(mailbox, pwd, server, login, password, folder):
    """ Encrypt the mailbox connection information using pwd """
    key = hashlib.sha256(pwd.encode()).digest()
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CFB, iv)
    info = [server, login, password, folder]
    with open(os.path.join(LOCAL_PATH, mailbox), 'wb') as fich:
        fich.write(iv)
        fich.write(cipher.encrypt("\n".join(info)))


# Images
ICON = os.path.join(LOCAL_PATH, "icon_mail.png")
IMAGE = os.path.join(PATH, "images", "mail.png")
ICON_48 = os.path.join(PATH, "images", "mail48.png")
IMAGE2 = os.path.join(PATH, "images", "mail.svg")
ADD = os.path.join(PATH, "images", "add.png")
DEL = os.path.join(PATH, "images", "del.png")
EDIT = os.path.join(PATH, "images", "edit.png")

def internet_on():
    try:
        check_output(["ping", "-c", "1", "www.google.com"])
        return True
    except CalledProcessError:
        return False

