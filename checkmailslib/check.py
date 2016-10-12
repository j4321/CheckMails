#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Checkmails - System tray unread mail checker
Copyright 2016 Juliette Monsel <j_4321@hotmail.fr>

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

from imaplib import IMAP4_SSL, IMAP4
from socket import gaierror
from threading import Thread
import crypt
from subprocess import Popen
from tkinter import Tk, PhotoImage, Toplevel, TclError
from tkinter.messagebox import showerror, askokcancel
from tkinter.ttk import Entry, Label, Button, Style
from PIL import Image, ImageDraw, ImageFont
from tktray import Icon
import os
from checkmailslib.constants import IMAGE, ICON, IMAGE2, LANG,save_config
from checkmailslib.constants import encrypt, decrypt, LOCAL_PATH, CONFIG, internet_on
from checkmailslib.manager import Manager
from checkmailslib.config import Config
from checkmailslib.about import About
_ = LANG.gettext

class CheckMails(Tk):
    """ System tray app that periodically looks for new mails. """
    def __init__(self):
        Tk.__init__(self)
        self.withdraw()
        # icon that will show up in the taskbar for every toplevel
        self.im_icon = PhotoImage(master=self, file=IMAGE)
        self.iconphoto(True, self.im_icon)
        # system tray icon
        self.img = PhotoImage(file=IMAGE)
        self.icon = Icon(self, image=self.img)
        self.icon.menu.add_command(label=_("Check"), command=self.check_mails)
        self.icon.menu.add_command(label=_("Reconnect"), command=self.reconnect)
        self.icon.menu.add_command(label=_("Suspend"), command=self.start_stop)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Change password"), command=self.change_password)
        self.icon.menu.add_command(label=_("Reset password"), command=self.reset_password)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Manage mailboxes"), command=self.manage_mailboxes)
        self.icon.menu.add_command(label=_("Preferences"), command=self.config)
        self.icon.menu.add_command(label=_("About"), command=self.about)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Quit"), command=self.quit)
        self.icon.bind('<Button-1>', self.display)

        self.style = Style(self)
        self.style.theme_use('clam')

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
        # connection, logout and check are done in separate threads for each
        # mailbox so that the system tray icon does not become unresponsive if
        # the process takes some time
        self.threads_connect = {}
        self.threads_logout = {}
        self.threads_check = {}
        # after callbacks id
        self.check_id = ''
        self.timer_id = ''
        self.notif_id = ''
        self.internet_id = ''
        # notification displayed when clicking on the icon
        self.notif = ''
        # retrieve mailbox login information from encrypted files
        self.get_info_conn()

        self.mainloop()

    def start_stop(self):
        """ Suspend checks """
        if self.icon.menu.entrycget(2, "label") == _("Suspend"):
            self.icon.after_cancel(self.check_id)
            self.icon.after_cancel(self.timer_id)
            self.icon.after_cancel(self.notif_id)
            self.icon.after_cancel(self.internet_id)
            self.img.configure(file=IMAGE)
            self.icon.menu.entryconfigure(2, label=_("Restart"))
            self.icon.menu.entryconfigure(0, state="disabled")
            self.icon.menu.entryconfigure(1, state="disabled")
        else:
            self.icon.menu.entryconfigure(2, label=_("Suspend"))
            self.icon.menu.entryconfigure(0, state="normal")
            self.icon.menu.entryconfigure(1, state="normal")
            self.reconnect()

    def about(self):
        """ Show about dialog """
        About(self)

    def reconnect(self):
        self.icon.after_cancel(self.check_id)
        for box in self.boxes:
            self.logout(box, True, True)
        self.check_id = self.icon.after(20000, self.launch_check, False)

    def display(self, event):
        if self.icon.menu.entrycget(2, "label") == _("Suspend"):
            notif = self.notif
            if not notif:
                notif = _("Checking...")
        else:
            notif = _("Check suspended")
        Popen(["notify-send", "-i", IMAGE2, _("Unread mails"), notif])

    def reset_conn(self):
        """ Logout from all mailboxes, reset all variables and reload all the data. """
        for box in self.boxes:
            self.logout(box)
        self.boxes = {}
        self.nb_unread = {box: 0 for box in self.info_conn}
        self.threads_connect = {}
        self.threads_reconnect = {}
        self.threads_check = {}
        self.icon.after_cancel(self.timer_id)
        self.icon.after_cancel(self.check_id)
        self.icon.after_cancel(self.notif_id)
        self.get_info_conn()

    def get_info_conn(self):
        """ Retrieve connection information from the encrypted files and
            launch checks (if they are noit suspended). """
        mailboxes = CONFIG.get("Mailboxes", "active").split(", ")
        while "" in mailboxes:
            mailboxes.remove("")
        self.info_conn = {}
        if self.pwd is None:
            if not os.path.exists(os.path.join(LOCAL_PATH, ".pwd")):
                self.set_password()
            else:
                self.ask_password()
        if self.pwd is not None:
            for box in mailboxes:
                server, login, password, folder = decrypt(box, self.pwd)
                self.info_conn[box] = (server, (login, password), folder)

        if not self.info_conn:
            Popen(["notify-send", "-i", IMAGE2, _("No active mailbox"), _("Use the mailbox manager to confugure a mailbox.")])
        elif self.icon.menu.entrycget(2, "label") == _("Suspend"):
            for box in self.info_conn:
                self.connect(box)
            self.icon.after_cancel(self.check_id)
            self.check_id = self.after(20000, self.launch_check, False)

    def change_icon(self, nbmail):
        """ Display the number of unread mails nbmail in the system tray icon. """
        nb = "%i" % nbmail
        im = Image.open(IMAGE)
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("/usr/share/fonts/TTF/LiberationSans-Bold.ttf", 10)
        draw.text((6//len(nb),4), nb, fill=(255,0,0), font=font)
        im.save(ICON)
        self.img.configure(file=ICON)

    def config(self):
        """ Open config dialog to set times and language. """
        Config(self)
        self.time = CONFIG.getint("General", "time")
        self.timeout = CONFIG.getint("General", "timeout")
        if self.icon.menu.entrycget(2, "label") == _("Suspend"):
            self.check_mails(False)

    def manage_mailboxes(self):
        """ Open the mailbox manager. """
        if self.pwd is None:
            if not os.path.exists(os.path.join(LOCAL_PATH, ".pwd")):
                self.set_password()
            else:
                self.ask_password()
        if self.pwd is not None:
            m = Manager(self, self.pwd)
            self.wait_window(m)
            self.reset_conn()

    def connect_mailbox(self, box):
        """ Connect to the mailbox box and select the folder. """
        try:
            print("Connecting to", box)
            serveur, loginfo, folder = self.info_conn[box]
            # reinitialize the connection if it takes too long
            timeout_id = self.after(self.timeout, self.logout, box, False, True)
            self.boxes[box] = IMAP4_SSL(serveur)
            self.boxes[box].login(*loginfo)
            self.boxes[box].select(folder)
            self.after_cancel(timeout_id)
            print("Connected to", box)

        except (IMAP4.error, ConnectionResetError, TimeoutError) as e:
            self.after_cancel(timeout_id)
            if e.args[0] in [b'Invalid login or password', b'Authenticate error', b'LOGIN failed']:
                # Identification error
                Popen(["notify-send", "-i", "dialog-error", _("Error"),
                       _("Incorrect login or password for %(mailbox)s") % {"mailbox": box}])
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
            else:
                # try to reconnect
                print(e)
                self.logout(box, reconnect=True)
        except gaierror as e:
            if e.args == (-2, 'Name or service not known'):
                # Either there is no internet connection or the IMAP server is wrong
                if internet_on():
                    Popen(["notify-send", "-i", "dialog-error",_("Error"),
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
                else:
                    Popen(["notify-send", "-i", "dialog-error",_("Error"),
                           _("No internet connection.")])
                    # cancel everything
                    self.icon.after_cancel(self.check_id)
                    self.icon.after_cancel(self.timer_id)
                    self.icon.after_cancel(self.notif_id)
                    self.icon.after_cancel(self.internet_id)
                    # periodically checks if the internet connection is turned on
                    self.internet_id = self.after(self.timeout, self.test_connection)
            else:
                # try to reconnect
                print(e)
                self.logout(box, reconnect=True)

        except ValueError:
            # Error sometimes raised when a connection process is interrupted by a logout process
            pass

    def test_connection(self):
        """ Launch mail check if there is an internet connection otherwise
            check again for an internet connection after self.timeout. """
        if internet_on():
            self.reset_conn()
        else:
            self.internet_id = self.icon.after(self.timeout, self.test_connection)

    def logout_mailbox(self, box, reconnect):
        """ Logout from box. If reconnect is True, launch connection once
            logout is done. """
        if box in self.boxes:
            mail = self.boxes[box]
            try:
                print('Logging out of', box)
                mail.logout()
                print('Logged out of', box)
            except (IMAP4.abort, OSError):
                # the connection attempt has aborted due to the logout
                pass
            if reconnect:
                self.connect(box)

    def connect(self, box):
        """ Launch the connection to the mailbox box in a thread """
        if not (box in self.threads_connect and self.threads_connect[box].isAlive()):
            self.threads_connect[box] = Thread(target=self.connect_mailbox,
                                                 name='connect_' + box,
                                                 daemon=True,
                                                 args=(box,))
            self.threads_connect[box].start()

    def logout(self, box, force=False, reconnect=False):
        """ Launch the logout from box in a thread. If force is True,
            launch the logout even if a logout process is active. If reconnect
            is True, launch the connection to box once the logout is done. """
        if force or not (box in self.threads_logout and self.threads_logout[box].isAlive()):
            self.threads_logout[box] = Thread(target=self.logout_mailbox,
                                                name='logout_' + box,
                                                daemon=True,
                                                args=(box,reconnect))
            self.threads_logout[box].start()


    def launch_check(self, force_notify=False):
        """ Check every 20 s if the login to all the mailboxes is done.
            Once it is the case, launch the unread mail check. """
        b = [self.threads_connect[box].isAlive() for box in self.threads_connect]
        if len(b) < len(self.info_conn) or True in b:
            print("waiting for connexion ...")
            self.icon.after_cancel(self.check_id)
            self.check_id = self.icon.after(20000, self.launch_check, force_notify)
        else:
            print("launching check")
            self.check_mails(force_notify)

    def check_mailbox(self, box):
        """ Look for unread mails in box """
        mail = self.boxes[box]
        # reinitialize the connection if it takes too long
        timeout_id = self.after(self.timeout, self.logout, box, True, True)
        print("collecting unread mails for", box)
        try:
            r, messages = mail.search(None, '(UNSEEN)')
            self.after_cancel(timeout_id)
            self.nb_unread[box] = len(messages[0].split())
            if self.nb_unread[box] > 0:
               self.notif += "%s : %i, " % (box, self.nb_unread[box])
            print("unread mails collected for", box)

        except (IMAP4.error, ConnectionResetError, TimeoutError) as e:
            print(e)
            self.after_cancel(timeout_id)
            if self.notif != _("Checking...") + "/n":
                notif = self.notif
                notif += "%s : %s, " % (box, _("Timed out, reconnecting"))
                Popen(["notify-send", "-i", IMAGE2, _("Unread mails"), notif])
                nbtot = 0
                for nb in self.nb_unread.values():
                    nbtot += nb
                self.change_icon(nbtot)
            self.logout(box, force=True, reconnect=True)



    def check_mails(self, force_notify=True):
        """ Check whether there are new mails. If force_notify is True,
            display a notification even if there is no unread mail. """
        self.notif = _("Checking...") + "\n"
        self.icon.after_cancel(self.timer_id)
        self.icon.after_cancel(self.notif_id)
        for box, mail in self.boxes.items():
            if not self.threads_connect[box].isAlive() and (not box in self.threads_check or not self.threads_check[box].isAlive()):
                self.threads_check[box] = Thread(target=self.check_mailbox,
                                                   name='check_' + box,
                                                   daemon=True,
                                                   args=(box,))
                self.threads_check[box].start()
        self.notif_id = self.icon.after(20000, self.notify_unread_mails, force_notify)
        self.timer_id = self.icon.after(self.time, self.check_mails, False)

    def notify_unread_mails(self, force_notify=True):
        """ Check every 20 s if the checks are done for all the mailboxes.
            If it is the case display the number of unread mails for each boxes.
            If force_notify is True, display a notification even if there is no
            unread mail. """
        b = [self.threads_check[box].isAlive() for box in self.threads_check]
        if len(b) < len(self.info_conn) or True in b:
            self.notif_id = self.icon.after(20000, self.notify_unread_mails, force_notify)
        else:
            if self.notif != _("Checking...") + "\n":
                self.notif = self.notif[:-2].split("\n")[1]
                Popen(["notify-send", "-i", IMAGE2, _("Unread mails"), self.notif])
            elif force_notify:
                Popen(["notify-send", "-i", IMAGE2, _("Unread mails"), _("No unread mail")])
                self.notif = _("No unread mail")
            else:
                self.notif = _("No unread mail")
            nbtot = 0
            for nb in self.nb_unread.values():
                nbtot += nb
            self.change_icon(nbtot)

    def quit(self):
        """ Logout from all the mailboxes and quit """
        for box in self.info_conn:
            self.logout(box)
        try:
            self.destroy()
        except TclError:
            # depending on the pending processes when the app is destroyed
            # a TclError: can't delete Tcl command is sometimes raised
            # I do not know how to prevent this so for now I just catch it
            # and do nothing
            pass

    def ask_password(self):
        """ Ask the master password in order to decrypt the mailbox config files """
        def ok(event=None):
            with open(os.path.join(LOCAL_PATH, '.pwd')) as fich:
                cryptedpwd = fich.read()
            pwd = getpwd.get()
            if crypt.crypt(pwd, cryptedpwd) == cryptedpwd:
                # passwords match
                top.destroy()
                self.pwd = pwd
            else:
                showerror(_('Error'), _('Incorrect password!'))
                getpwd.delete(0,"end")
        top = Toplevel(self)
        top.title(_("Password"))
        top.resizable(False, False)
        Label(top, text=_("Enter password")).pack(padx=10, pady=(10,4))
        getpwd = Entry(top, show='*', justify='center')
        getpwd.pack(padx=10, pady=4)
        Button(top, text="Ok", command=ok).pack(padx=10, pady=(4,10))
        getpwd.bind("<Key-Return>", ok)
        getpwd.focus_set()
        self.wait_window(top)

    def set_password(self):
        """ Set the master password used to encrypt the mailbox config files """
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
            else:
                showerror(_('Error'), _('Passwords do not match!'))

        top = Toplevel(self)
        top.iconphoto(True, self.im_icon)
        top.title(_("Set password"))
        top.resizable(False, False)
        Label(top, text=_("Enter master password")).pack(padx=10, pady=(4,10))
        getpwd = Entry(top, show='*', justify='center')
        getpwd.pack(padx=10, pady=4)
        Label(top, text=_("Confirm master password")).pack(padx=10, pady=4)
        confpwd = Entry(top, show='*', justify='center')
        confpwd.pack(padx=10, pady=4)
        Button(top, text="Ok", command=ok).pack(padx=10, pady=(4,10))
        confpwd.bind("<Key-Return>", ok)
        getpwd.focus_set()
        self.wait_window(top)

    def change_password(self):
        """ Change the master password: decrypt all the mailbox config files
            using the old password and encrypt them with the new. """
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
                        encrypt(mailbox, pwd, server, login, password, folder)
                    self.pwd = pwd
                    top.destroy()
                    return pwd
                else:
                    showerror(_('Error'), _('Passwords do not match!'))
            else:
                showerror(_('Error'), _('Incorrect password!'))

        top = Toplevel(self)
        top.iconphoto(True, self.im_icon)
        top.resizable(False, False)
        Label(top, text=_("Old password")).pack(padx=10, pady=(10,4))
        oldpwd = Entry(top, show='*', justify='center')
        oldpwd.pack(padx=10, pady=4)
        Label(top, text=_("New password")).pack(padx=10, pady=4)
        newpwd = Entry(top, show='*', justify='center')
        newpwd.pack(padx=10, pady=4)
        Label(top, text=_("Confirm password")).pack(padx=10, pady=4)
        confpwd = Entry(top, show='*', justify='center')
        confpwd.pack(padx=10, pady=4)
        Button(top, text="Ok", command=ok).pack(padx=10, pady=(4,10))
        confpwd.bind("<Key-Return>", ok)
        oldpwd.focus_set()
        self.wait_window(top)

    def reset_password(self):
        """ Reset the master password and delete all the mailboxes config files
            since they cannot be decrypted without the password """
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
            self.set_password()




