# -*- coding:Utf-8 -*-
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

Main class
"""


import os
import traceback
import logging
import email
from email import policy
from imaplib import IMAP4_SSL, IMAP4
from socket import gaierror
from threading import Thread
from queue import Queue
import crypt
try:
    from subprocess import run
except ImportError:
    from subprocess import call as run
from tkinter import Tk, Toplevel, TclError
from tkinter.messagebox import showerror, askokcancel
from tkinter.ttk import Entry, Label, Button, Style

from PIL import Image, ImageDraw, ImageFont

import checkmailslib.constants as cst
from checkmailslib.trayicon import TrayIcon
from checkmailslib.constants import IMAGE, ICON, IMAGE2, save_config, FONTSIZE,\
    encrypt, decrypt, LOCAL_PATH, CONFIG, internet_on, TTF_FONTS, ICON_48, \
    PhotoImage
from checkmailslib.manager import Manager, EditMailbox
from checkmailslib.config import Config
from checkmailslib.about import About
from checkmailslib.messagebox import show_failed_auth_msg
from checkmailslib.version_check import UpdateChecker


class CheckMails(Tk):
    """System tray app that periodically looks for new mails."""
    def __init__(self):
        Tk.__init__(self, className="CheckMails")
        self.withdraw()
        logging.info('Starting checkmails')
        # icon that will show up in the taskbar for every toplevel
        self.im_icon = PhotoImage(master=self, file=ICON_48)
        self.iconphoto(True, self.im_icon)

        # system tray icon
        self.icon = TrayIcon(IMAGE)
        self.icon.add_menu_item(label=_("Details"), command=self.display)
        self.icon.add_menu_item(label=_("Check"), command=self.check_mails)
        self.icon.add_menu_item(label=_("Reconnect"),
                                command=self.reconnect)
        self.icon.add_menu_item(label=_("Suspend"), command=self.start_stop)
        self.icon.add_menu_separator()
        self.icon.add_menu_item(label=_("Change password"),
                                command=self.change_password)
        self.icon.add_menu_item(label=_("Reset password"),
                                command=self.reset_password)
        self.icon.add_menu_separator()
        self.icon.add_menu_item(label=_("Manage mailboxes"),
                                command=self.manage_mailboxes)
        self.icon.add_menu_item(label=_("Preferences"), command=self.config)
        self.icon.add_menu_separator()
        self.icon.add_menu_item(label=_("Check for updates"),
                                command=lambda: UpdateChecker(self, True))
        self.icon.add_menu_item(label=_("About"),
                                command=lambda: About(self))
        self.icon.add_menu_separator()
        self.icon.add_menu_item(label=_("Quit"), command=self.quit)
        self.icon.loop(self)
        self.icon.bind_left_click(self.display)

        self.style = Style(self)
        self.style.theme_use('clam')
        bg = self.cget("background")
        self.style.configure("TLabel", background=bg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TButton", background=bg)
        self.style.configure("TCheckbutton", background=bg)
        self.style.configure("TMenubutton", background=bg)
        self.style.map('TCheckbutton',
                       indicatorbackground=[('pressed', '#dcdad5'),
                                            ('!disabled', 'alternate', 'white'),
                                            ('disabled', 'alternate', '#a0a0a0'),
                                            ('disabled', '#dcdad5')])

        # master password
        self.pwd = None
        # login info
        self.info_conn = {}
        # time between two checks
        self.time = CONFIG.getint("General", "time")
        # maximum time for login / check before the connection is reset
        self.timeout = CONFIG.getint("General", "timeout")

        self.boxes = {}
        # number of unread mails for each mailbox
        self.nb_unread = {box: 0 for box in self.info_conn}
        self.unread_msgs = {box: set() for box in self.info_conn}
        # connection, logout and check are done in separate threads for each
        # mailbox so that the system tray icon does not become unresponsive if
        # the process takes some time
        self.threads_connect = {}
        self.threads_logout = {}
        self.threads_check = {}
        self.login_err_queue = Queue()
        # after callbacks id
        self.check_id = ''
        self.timer_id = ''
        self.notif_id = ''
        self.internet_id = ''
        self.notify_no_internet = True  # avoid multiple notification of No Internet connection
        # notification displayed when clicking on the icon
        self.notif = ''
        # retrieve mailbox login information from encrypted files
        self.get_info_conn()

        if CONFIG.getboolean("General", "check_update"):
            UpdateChecker(self)

        # replace Ctrl+A binding by select all for all entries
        self.bind_class("TEntry", "<Control-a>", self.select_all_entry)

    def select_all_entry(self, event):
        event.widget.selection_range(0, "end")

    def report_callback_exception(self, *args):
        """Log exceptions."""
        if args[0] is KeyboardInterrupt:
            logging.error("KeyboardInterrupt")
            self.quit()
        err = "".join(traceback.format_exception(*args))
        logging.error(err)

    def start_stop(self):
        """Suspend checks."""
        if self.icon.get_item_label(3) == _("Suspend"):
            try:
                self.after_cancel(self.check_id)
            except ValueError:
                pass
            try:
                self.after_cancel(self.timer_id)
            except ValueError:
                pass
            try:
                self.after_cancel(self.notif_id)
            except ValueError:
                pass
            try:
                self.after_cancel(self.internet_id)
            except ValueError:
                pass
            self.icon.change_icon(IMAGE, "checkmails suspended")
            self.icon.set_item_label(3, _("Restart"))
            self.icon.disable_item(1)
            self.icon.disable_item(2)
            logging.info("CheckMails suspended")
        else:
            self.icon.set_item_label(3, _("Suspend"))
            self.icon.enable_item(1)
            self.icon.enable_item(2)
            self.reconnect()
            logging.info("CheckMails restarted")

    def reconnect(self):
        self.notify_no_internet = True
        if self.pwd is None:
            self.get_info_conn()
            if self.pwd is None:
                return
        try:
            self.after_cancel(self.check_id)
        except ValueError:
            pass
        self.nb_unread = {box: 0 for box in self.info_conn}
        for box in self.boxes:
            self.logout(box, True, True)
        self.check_id = self.after(20000, self.launch_check, False)

    def display(self):
        if self.icon.get_item_label(3) == _("Suspend"):
            notif = self.notif
            if not notif:
                notif = _("Checking...")
        else:
            notif = _("Check suspended")
        run(["notify-send", "-i", IMAGE2, _("Unread mails"), notif])

    def reset_conn(self):
        """Logout from all mailboxes, reset all variables and reload all the data."""
        for box in self.boxes:
            self.logout(box)
        self.boxes = {}
        self.nb_unread = {box: 0 for box in self.info_conn}
        self.threads_connect = {}
        self.threads_reconnect = {}
        self.threads_check = {}
        try:
            self.after_cancel(self.timer_id)
        except ValueError:
            pass
        try:
            self.after_cancel(self.check_id)
        except ValueError:
            pass
        try:
            self.after_cancel(self.notif_id)
        except ValueError:
            pass
        self.get_info_conn()

    def get_info_conn(self):
        """
        Retrieve connection information from the encrypted files and
        launch checks (if they are noit suspended).
        """
        mailboxes = CONFIG.get("Mailboxes", "active").split(", ")
        while "" in mailboxes:
            mailboxes.remove("")
        self.info_conn = {}
        if self.pwd is None:
            if not os.path.exists(os.path.join(LOCAL_PATH, ".pwd")):
                self.set_password()
            else:
                self.ask_password()

        if self.pwd is None:
            self.notif = _("Login required")
            return

        for box in mailboxes:
            server, login, password, folder = decrypt(box, self.pwd)
            if server is not None:
                self.info_conn[box] = (server, (login, password), folder)
                if box not in self.unread_msgs:
                        self.unread_msgs[box] = set()
        if not self.info_conn:
            self.notif = _("No active mailbox")
            run(["notify-send", "-i", IMAGE2, _("No active mailbox"), _("Use the mailbox manager to configure a mailbox.")])
        elif self.icon.get_item_label(3) == _("Suspend"):
            self.notif = ""
            for box in self.info_conn:
                self.connect(box)
            try:
                self.after_cancel(self.check_id)
            except ValueError:
                pass
            self.check_id = self.after(20000, self.launch_check, False)

    def change_icon(self, nbmail):
        """Display the number of unread mails nbmail in the system tray icon."""
        nb = "%i" % nbmail
        im = Image.open(IMAGE)
        W, H = im.size
        draw = ImageDraw.Draw(im)
        font_path = TTF_FONTS[CONFIG.get("General", "font")]
        try:
            font = ImageFont.truetype(font_path, FONTSIZE)
            w, h = draw.textsize(nb, font=font)
            draw.text(((W - w) / 2, (H - h) / 2), nb, fill=(255, 0, 0),
                      font=font)
        except OSError:
            w, h = draw.textsize(nb)
            draw.text(((W - w) / 2, (H - h) / 2), nb, fill=(255, 0, 0))
        im.save(ICON)
        self.icon.change_icon(ICON, "checkmails %s" % nb)

    def config(self):
        """Open config dialog to set times and language."""
        Config(self)
        self.time = CONFIG.getint("General", "time")
        self.timeout = CONFIG.getint("General", "timeout")
        if self.icon.get_item_label(3) == _("Suspend"):
            self.check_mails(False)

    def manage_mailboxes(self):
        """Open the mailbox manager."""
        if self.pwd is None:
            if not os.path.exists(os.path.join(LOCAL_PATH, ".pwd")):
                self.set_password()
            else:
                self.ask_password()
        if self.pwd is not None:
            m = Manager(self, self.pwd)
            m.grab_set()
            self.wait_window(m)
            self.reset_conn()

    def connect_mailbox(self, box):
        """Connect to the mailbox box and select the folder."""
        try:
            logging.info("Connecting to %s" % box)
            serveur, loginfo, folder = self.info_conn[box]
            # reinitialize the connection if it takes too long
            timeout_id = self.after(self.timeout, self.timed_out, box, False, True)
            self.boxes[box] = IMAP4_SSL(serveur)
            self.boxes[box].login(*loginfo)
            self.boxes[box].select(folder)
            try:
                self.after_cancel(timeout_id)
            except ValueError:
                pass
            logging.info("Connected to %s" % box)

        except (IMAP4.error, ConnectionResetError, TimeoutError) as e:
            try:
                self.after_cancel(timeout_id)
            except ValueError:
                pass
            if e.args[0] in [b'Invalid login or password',
                             b'Authenticate error',
                             b'Login failed: authentication failure',
                             b'LOGIN failed']:
                # Identification error
                logging.error("Incorrect login or password for %(mailbox)s" % {"mailbox": box})
                self.login_err_queue.put(box)
            else:
                # try to reconnect
                logging.error('%s: %s' % (box, e))
                self.logout(box, reconnect=True)
        except gaierror as e:
            if e.errno == -2:
                # Either there is No Internet connection or the IMAP server is wrong
                if internet_on():
                    run(["notify-send", "-i", "dialog-error", _("Error"),
                         _("Wrong IMAP server for %(mailbox)s.") % {"mailbox": box}])
                    # remove box from the active mailboxes
                    active = CONFIG.get("Mailboxes", "active").split(", ")
                    inactive = CONFIG.get("Mailboxes", "inactive").split(", ")
                    while "" in active:
                        active.remove("")
                    while "" in inactive:
                        inactive.remove("")
                    active.remove(box)
                    inactive.append(box)
                    CONFIG.set("Mailboxes", "active", ", ".join(active))
                    CONFIG.set("Mailboxes", "inactive", ", ".join(inactive))
                    logging.error("Wrong IMAP server for %(mailbox)s." % {"mailbox": box})
                else:
                    if self.notify_no_internet:
                        run(["notify-send", "-i", "dialog-error", _("Error"),
                             _("No Internet connection.")])
                        self.notify_no_internet = False
                    logging.warning("No Internet connection")
                    # cancel everything
                    try:
                        self.after_cancel(self.check_id)
                    except ValueError:
                        pass
                    try:
                        self.after_cancel(self.timer_id)
                    except ValueError:
                        pass
                    try:
                        self.after_cancel(self.notif_id)
                    except ValueError:
                        pass
                    try:
                        self.after_cancel(self.internet_id)
                    except ValueError:
                        pass
                    # periodically checks if the internet connection is turned on
                    self.internet_id = self.after(self.timeout, self.test_connection)
            else:
                # try to reconnect
                logging.exception(str(type(e)))
                run(["notify-send", "-i", "dialog-error", _("Error"),
                     traceback.format_exc()])
                self.logout(box, reconnect=True)

        except ValueError:
            # Error sometimes raised when a connection process is interrupted by a logout process
            pass

    def test_connection(self):
        """
        Launch mail check if there is an internet connection otherwise
        check again for an internet connection after self.timeout.
        """
        if internet_on():
            self.reset_conn()
            logging.info("Connected to Internet")
            self.notify_no_internet = True
        else:
            self.internet_id = self.after(self.timeout, self.test_connection)

    def logout_mailbox(self, box, reconnect):
        """
        Logout from box. If reconnect is True, launch connection once
        logout is done.
        """
        if box in self.boxes:
            mail = self.boxes[box]
            try:
                logging.info('Logging out of %s' % box)
                mail.logout()
                logging.info('Logged out of %s' % box)
            except (IMAP4.abort, OSError):
                # the connection attempt has aborted due to the logout
                pass
            if reconnect:
                self.connect(box)

    def connect(self, box):
        """Launch the connection to the mailbox box in a thread """
        if not (box in self.threads_connect and self.threads_connect[box].is_alive()):
            self.threads_connect[box] = Thread(target=self.connect_mailbox,
                                               name='connect_' + box,
                                               daemon=True,
                                               args=(box,))
            self.threads_connect[box].start()

    def logout(self, box, force=False, reconnect=False):
        """
        Launch the logout from box in a thread. If force is True,
        launch the logout even if a logout process is active. If reconnect
        is True, launch the connection to box once the logout is done.
        """
        if force or not (box in self.threads_logout and self.threads_logout[box].is_alive()):
            self.threads_logout[box] = Thread(target=self.logout_mailbox,
                                              name='logout_' + box,
                                              daemon=True,
                                              args=(box, reconnect))
            self.threads_logout[box].start()

    def timed_out(self, box, force=False, reconnect=False):
        """Check Internet connection if check timed out."""
        if internet_on():
            self.logout(box, force, reconnect)
        else:
            if self.notify_no_internet:
                run(["notify-send", "-i", "dialog-error", _("Error"),
                     _("No Internet connection.")])
                self.notify_no_internet = False
            logging.warning("No Internet connection")
            # cancel everything
            try:
                self.after_cancel(self.check_id)
            except ValueError:
                pass
            try:
                self.after_cancel(self.timer_id)
            except ValueError:
                pass
            try:
                self.after_cancel(self.notif_id)
            except ValueError:
                pass
            try:
                self.after_cancel(self.internet_id)
            except ValueError:
                pass
            # periodically checks if the internet connection is turned on
            self.internet_id = self.after(self.timeout, self.test_connection)

    def launch_check(self, force_notify=False):
        """
        Check every 20 s if the login to all the mailboxes is done.
        Once it is the case, launch the unread mail check.
        """
        b = [self.threads_connect[box].is_alive() for box in self.threads_connect]
        if len(b) < len(self.info_conn) or True in b:
            logging.info("Waiting for connexion ...")
            try:
                self.after_cancel(self.check_id)
            except ValueError:
                pass
            self.check_id = self.after(20000, self.launch_check, force_notify)
        else:
            logging.info("Launching check")
            if not self.login_err_queue.empty():
                correct = False
                while not self.login_err_queue.empty():
                    box = self.login_err_queue.get()
                    action = show_failed_auth_msg(self, box)
                    if action == 'correct':
                        dialog = EditMailbox(self, self.pwd, box)
                        self.wait_window(dialog)
                        self.connect(box)
                        correct = dialog.name or correct
                    else:
                        # remove box from the active mailboxes
                        del(self.boxes[box])
                        active = CONFIG.get("Mailboxes", "active").split(", ")
                        inactive = CONFIG.get("Mailboxes", "inactive").split(", ")
                        while "" in active:
                            active.remove("")
                        while "" in inactive:
                            inactive.remove("")
                        active.remove(box)
                        inactive.append(box)
                        CONFIG.set("Mailboxes", "active", ", ".join(active))
                        CONFIG.set("Mailboxes", "inactive", ", ".join(inactive))
                if correct:
                    self.after_cancel(self.check_id)
                    self.check_id = self.after(20000, self.launch_check, force_notify)
                else:
                    self.check_mails(force_notify)
            else:
                self.check_mails(force_notify)

    def check_mailbox(self, box):
        """Look for unread mails in box."""
        mail = self.boxes[box]
        # reinitialize the connection if it takes too long
        timeout_id = self.after(self.timeout, self.timed_out, box, True, True)
        logging.info("Collecting unread mails for %s" % box)
        try:
            r, messages = mail.search(None, '(UNSEEN)')
            try:
                self.after_cancel(timeout_id)
            except ValueError:
                pass
            msgs = set(messages[0].split())
            self.nb_unread[box] = len(msgs)
            if msgs:
                self.notif += "%s : %i, " % (box, self.nb_unread[box])
                if CONFIG.getboolean('General', 'notify_new_unread', fallback=True):
                    for msg in sorted(msgs.difference(self.unread_msgs[box])):
                        res, data = mail.fetch(msg, '(BODY.PEEK[HEADER])')
                        if res == 'OK':
                            m = email.message_from_bytes(data[0][1], policy=policy.default)
                            title = "{} [{}]".format(m['Subject'], box)
                            info = _("From: {From}\nDate: {Date}").format(Date=m['Date'],
                                                                          From=m['From'])
                            run(["notify-send", "-i", IMAGE2, title, info])
                self.unread_msgs[box] = msgs
            else:
                self.unread_msgs[box].clear()

            logging.info("Unread mails collected for %s" % box)

        except (IMAP4.error, ConnectionResetError, TimeoutError) as e:
            try:
                self.after_cancel(timeout_id)
            except ValueError:
                pass
            if self.notif != _("Checking...") + "/n":
                logging.error('%s: %s' % (box, e))
                if CONFIG.getboolean('General', 'notify_nb_unread', fallback=True):
                    notif = self.notif
                    notif += "%s : %s, " % (box, _("Timed out, reconnecting"))
                    run(["notify-send", "-i", IMAGE2, _("Unread mails"), notif])
                nbtot = 0
                for b, nb in self.nb_unread.items():
                    if b != box:
                        nbtot += nb
                self.change_icon(nbtot)
            else:
                logging.exception(str(type(e)))
            self.logout(box, force=True, reconnect=True)

    def check_mails(self, force_notify=True):
        """
        Check whether there are new mails. If force_notify is True,
        display a notification even if there is no unread mail.
        """
        if self.pwd is None:
            self.get_info_conn()
            if self.pwd is None:
                return
        self.notif = _("Checking...") + "\n"
        try:
            self.after_cancel(self.timer_id)
        except ValueError:
            pass
        try:
            self.after_cancel(self.notif_id)
        except ValueError:
            pass
        for box, mail in self.boxes.items():
            if not self.threads_connect[box].is_alive() and (box not in self.threads_check or not self.threads_check[box].is_alive()):
                self.threads_check[box] = Thread(target=self.check_mailbox,
                                                 name='check_' + box,
                                                 daemon=True,
                                                 args=(box,))
                self.threads_check[box].start()
        self.notif_id = self.after(20000, self.notify_unread_mails, force_notify)
        self.timer_id = self.after(self.time, self.check_mails, False)

    def notify_unread_mails(self, force_notify=True):
        """
        Check every 20 s if the checks are done for all the mailboxes.
        If it is the case display the number of unread mails for each boxes.
        If force_notify is True, display a notification even if there is no
        unread mail.
        """
        b = [self.threads_check[box].is_alive() for box in self.threads_check]
        if len(b) < len(self.info_conn) or True in b:
            self.notif_id = self.after(20000, self.notify_unread_mails, force_notify)
        else:
            if self.notif != _("Checking...") + "\n":
                try:
                    self.notif = self.notif[:-2].split("\n")[1]
                except IndexError:
                    pass
                if force_notify or CONFIG.getboolean("General", "notify_nb_unread", fallback=True):
                    run(["notify-send", "-i", IMAGE2, _("Unread mails"), self.notif])
            elif force_notify:
                run(["notify-send", "-i", IMAGE2, _("Unread mails"), _("No unread mail")])
                self.notif = _("No unread mail")
            else:
                self.notif = _("No unread mail")
            nbtot = 0
            for nb in self.nb_unread.values():
                nbtot += nb
            self.change_icon(nbtot)

    def quit(self):
        """Logout from all the mailboxes and quit."""
        for box in self.info_conn:
            self.logout(box)
        try:
            self.after_cancel(self.loop_id)
            self.destroy()
        except (TclError, ValueError):
            # depending on the pending processes when the app is destroyed
            # a TclError: can't delete Tcl command is sometimes raised
            # I do not know how to prevent this so for now I just catch it
            # and do nothing
            pass

    def ask_password(self):
        """Ask the master password in order to decrypt the mailbox config files."""
        with open(os.path.join(LOCAL_PATH, '.pwd')) as fich:
            cryptedpwd = fich.read()

        if cst.KEYRING:  # try getting password from keyring
            pwd = cst.get_pwd_from_keyring()
            if pwd is not None and crypt.crypt(pwd, cryptedpwd) == cryptedpwd:
                # passwords match
                logging.info('Authentication successful')
                self.pwd = pwd
                return

        def ok(event=None):
            pwd = getpwd.get()
            if crypt.crypt(pwd, cryptedpwd) == cryptedpwd:
                # passwords match
                top.destroy()
                logging.info('Authentication successful')
                self.pwd = pwd
            else:
                showerror(_('Error'), _('Incorrect password!'))
                logging.warning('Authentication failed')
                getpwd.delete(0, "end")

        top = Toplevel(self, class_="CheckMails")
        top.title(_("Password"))
        top.resizable(False, False)
        Label(top, text=_("Enter password")).pack(padx=10, pady=(10, 4))
        getpwd = Entry(top, show='*', justify='center')
        getpwd.pack(padx=10, pady=4)
        Button(top, text="Ok", command=ok).pack(padx=10, pady=(4, 10))
        getpwd.bind("<Key-Return>", ok)
        getpwd.focus_set()
        self.wait_window(top)

    def set_password(self):
        """Set the master password used to encrypt the mailbox config files."""

        def ok(event=None):
            pwd = getpwd.get()
            pwd2 = confpwd.get()
            if pwd == pwd2:
                # passwords match
                cryptedpwd = crypt.crypt(pwd, crypt.mksalt(crypt.METHOD_SHA512))
                with open(os.path.join(LOCAL_PATH, '.pwd'), "w") as fich:
                    fich.write(cryptedpwd)
                top.destroy()
                self.pwd = pwd
                logging.info('New password set')
                if cst.KEYRING:  # try storing password in keyring
                    cst.store_pwd_in_keyring(pwd)
            else:
                showerror(_('Error'), _('Passwords do not match!'))

        top = Toplevel(self, class_="CheckMails")
        top.iconphoto(True, self.im_icon)
        top.title(_("Set password"))
        top.resizable(False, False)
        Label(top, text=_("Enter master password")).pack(padx=10, pady=(4, 10))
        getpwd = Entry(top, show='*', justify='center')
        getpwd.pack(padx=10, pady=4)
        Label(top, text=_("Confirm master password")).pack(padx=10, pady=4)
        confpwd = Entry(top, show='*', justify='center')
        confpwd.pack(padx=10, pady=4)
        Button(top, text="Ok", command=ok).pack(padx=10, pady=(4, 10))
        confpwd.bind("<Key-Return>", ok)
        getpwd.focus_set()
        self.wait_window(top)

    def change_password(self):
        """
        Change the master password: decrypt all the mailbox config files
        using the old password and encrypt them with the new.
        """

        def ok(event=None):
            with open(os.path.join(LOCAL_PATH, '.pwd')) as fich:
                cryptedpwd = fich.read()
            old = oldpwd.get()
            pwd = newpwd.get()
            pwd2 = confpwd.get()
            if crypt.crypt(old, cryptedpwd) == cryptedpwd:
                # passwords match
                if pwd == pwd2:
                    # new passwords match
                    cryptedpwd = crypt.crypt(pwd, crypt.mksalt(crypt.METHOD_SHA512))
                    with open(os.path.join(LOCAL_PATH, '.pwd'), "w") as fich:
                        fich.write(cryptedpwd)
                    mailboxes = CONFIG.get("Mailboxes", "active").split(", ") + CONFIG.get("Mailboxes", "inactive").split(", ")
                    while "" in mailboxes:
                        mailboxes.remove("")
                    for mailbox in mailboxes:
                        server, login, password, folder = decrypt(mailbox, old)
                        if server is not None:
                            encrypt(mailbox, pwd, server, login, password, folder)
                    self.pwd = pwd
                    top.destroy()
                    logging.info('Password changed')
                    if cst.KEYRING:  # try storing password in keyring
                        cst.store_pwd_in_keyring(pwd)
                    return
                showerror(_('Error'), _('Passwords do not match!'))
            showerror(_('Error'), _('Incorrect password!'))

        top = Toplevel(self, class_="CheckMails")
        top.iconphoto(True, self.im_icon)
        top.resizable(False, False)
        Label(top, text=_("Old password")).pack(padx=10, pady=(10, 4))
        oldpwd = Entry(top, show='*', justify='center')
        oldpwd.pack(padx=10, pady=4)
        Label(top, text=_("New password")).pack(padx=10, pady=4)
        newpwd = Entry(top, show='*', justify='center')
        newpwd.pack(padx=10, pady=4)
        Label(top, text=_("Confirm password")).pack(padx=10, pady=4)
        confpwd = Entry(top, show='*', justify='center')
        confpwd.pack(padx=10, pady=4)
        Button(top, text="Ok", command=ok).pack(padx=10, pady=(4, 10))
        confpwd.bind("<Key-Return>", ok)
        oldpwd.focus_set()
        self.wait_window(top)

    def reset_password(self):
        """
        Reset the master password and delete all the mailboxes config files
        since they cannot be decrypted without the password.
        """
        rep = askokcancel(_("Confirmation"), _("The reset of the password will erase all the stored mailbox connection information"), icon="warning")
        if rep:
            mailboxes = CONFIG.get("Mailboxes", "active").split(", ") + CONFIG.get("Mailboxes", "inactive").split(", ")
            while "" in mailboxes:
                mailboxes.remove("")
            CONFIG.set("Mailboxes", "active", "")
            CONFIG.set("Mailboxes", "inactive", "")
            save_config()
            for mailbox in mailboxes:
                os.remove(os.path.join(LOCAL_PATH, mailbox))
            logging.info('Reset')
            self.set_password()
