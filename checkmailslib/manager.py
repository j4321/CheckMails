#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CheckMails - System tray unread mail checker
Copyright 2016-2018 Juliette Monsel <j_4321@protonmail.com>

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

Mailbox Manager
"""


import os
from tkinter import Toplevel
from tkinter.ttk import Button, Entry, Label, Checkbutton, Frame

from checkmailslib.constants import encrypt, decrypt, LOCAL_PATH, CONFIG,\
    save_config, ADD, DEL, EDIT, PhotoImage


class Manager(Toplevel):
    """Mailbox Manager."""
    def __init__(self, master, pwd):
        """Create the mailbox manager dialog."""
        Toplevel.__init__(self, master, class_="CheckMails")
        self.title(_("Mailbox Manager"))
        self.minsize(200, 10)
        self.pwd = pwd
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.im_add = PhotoImage(master=self, file=ADD)
        self.im_del = PhotoImage(master=self, file=DEL)
        self.im_edit = PhotoImage(master=self, file=EDIT)
        self.mailboxes = {}
        active = CONFIG.get("Mailboxes", "active").split(", ")
        inactive = CONFIG.get("Mailboxes", "inactive").split(", ")
        while "" in active:
            active.remove("")
        while "" in inactive:
            inactive.remove("")
        active.sort()
        inactive.sort()
        self.frame = Frame(self)
        self.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.grid(row=0, column=0, padx=10, pady=10, sticky="eswn")
        i = -1
        for i, box in enumerate(active):
            c = Checkbutton(self.frame)
            c.state(('selected',))
            c.grid(row=i, column=0, pady=4, padx=(4, 0))
            l = Label(self.frame, text=box)
            l.grid(row=i, column=1, padx=4, pady=4)
            b_edit = Button(self.frame, image=self.im_edit, width=1,
                            command=lambda m=box: self.mailbox_info(m))
            b_edit.grid(row=i, column=2, padx=4, pady=4)
            b_del = Button(self.frame, image=self.im_del, width=1,
                           command=lambda m=box: self.del_mailbox(m))
            b_del.grid(row=i, column=3, padx=4, pady=4)
            self.mailboxes[box] = [c, l, b_edit, b_del]
        for box in inactive:
            i += 1
            c = Checkbutton(self.frame)
            c.grid(row=i, column=0, pady=4, padx=(4, 0))
            l = Label(self.frame, text=box)
            l.grid(row=i, column=1, padx=4, pady=4)
            b_edit = Button(self.frame, image=self.im_edit, width=1,
                            command=lambda m=box: self.mailbox_info(m))
            b_edit.grid(row=i, column=2, padx=4, pady=4)
            b_del = Button(self.frame, image=self.im_del, width=1,
                           command=lambda m=box: self.del_mailbox(m))
            b_del.grid(row=i, column=3, padx=4, pady=4)
            self.mailboxes[box] = [c, l, b_edit, b_del]

        self.b_add = Button(self.frame, image=self.im_add, command=self.mailbox_info, width=1)
        self.b_add.grid(row=i + 1, column=0, columnspan=4, pady=4, padx=4, sticky='w')

    def quit(self):
        """Save configuration and destroy the dialog."""
        active = []
        inactive = []
        for box, (c, l, b1, b2) in self.mailboxes.items():
            if "selected" in c.state():
                active.append(box)
            else:
                inactive.append(box)
        CONFIG.set("Mailboxes", "active", ", ".join(active))
        CONFIG.set("Mailboxes", "inactive", ", ".join(inactive))
        save_config()
        self.destroy()

    def del_mailbox(self, mailbox):
        """Delete the mailbox."""
        try:
            os.remove(os.path.join(LOCAL_PATH, mailbox))
        except FileNotFoundError:
            pass
        c, l, b_edit, b_del = self.mailboxes[mailbox]
        del(self.mailboxes[mailbox])
        c.grid_forget()
        l.grid_forget()
        b_edit.grid_forget()
        b_del.grid_forget()

    def mailbox_info(self, mailbox=""):
        """GUI to add or modify a mailbox login information."""

        def on_click(event):
            event.widget.focus_set()
            event.widget.selection_range(0, 'end')
            event.widget.unbind('<1>')
            return "break"

        def save(event=None):
            name = name_entry.get().strip()
            if not mailbox:
                # new mailbox
                i = self.b_add.grid_info()['row']
                self.b_add.grid_configure(row=i + 1)
                c = Checkbutton(self.frame)
                c.state(('selected',))
                c.grid(row=i, column=0, pady=4, padx=(4, 0))
                l = Label(self.frame, text=name)
                l.grid(row=i, column=1, padx=4, pady=4)
                b_edit = Button(self.frame, image=self.im_edit, width=1,
                                command=lambda m=name: self.mailbox_info(m))
                b_edit.grid(row=i, column=2, padx=4, pady=4)
                b_del = Button(self.frame, image=self.im_del, width=1,
                               command=lambda m=name: self.del_mailbox(m))
                b_del.grid(row=i, column=3, padx=4, pady=4)
                self.mailboxes[name] = [c, l, b_edit, b_del]
            elif name != mailbox:
                # change name of mailbox
                os.remove(os.path.join(LOCAL_PATH, mailbox))
                c, l, b_edit, b_del = self.mailboxes[mailbox]
                del(self.mailboxes[mailbox])
                l.configure(text=name)
                b_edit.configure(command=lambda m=name: self.mailbox_info(m))
                b_del.configure(command=lambda m=name: self.del_mailbox(m))
                self.mailboxes[name] = [c, l, b_edit, b_del]

            encrypt(name, self.pwd, server_entry.get().strip(),
                    login_entry.get().strip(), password_entry.get().strip(),
                    folder_entry.get().strip())
            top.destroy()

        top = Toplevel(self, class_="CheckMails")
        top.title(_("Login information"))
        top.transient(self)
        top.resizable(False, False)
        name_entry = Entry(top, justify='center', width=32)
        server_entry = Entry(top, justify='center', width=32)
        login_entry = Entry(top, justify='center', width=32)
        password_entry = Entry(top, show='*', justify='center', width=32)
        folder_entry = Entry(top, justify='center', width=32)
        if mailbox:
            name_entry.insert(0, mailbox)
            server, login, password, folder = decrypt(mailbox, self.pwd)
            if server is None:
                top.destroy()
                self.del_mailbox(mailbox)
                return
            server_entry.insert(0, server)
            login_entry.insert(0, login)
            password_entry.insert(0, password)
            folder_entry.insert(0, folder)
        else:
            name_entry.insert(0, "Mailbox name")
            server_entry.insert(0, "IMAP.mailbox.com")
            login_entry.insert(0, "myaddress@mailbox.com")
            folder_entry.insert(0, "inbox")
            name_entry.bind("<1>", on_click)
            server_entry.bind("<1>", on_click)
            login_entry.bind("<1>", on_click)
            password_entry.bind("<1>", on_click)
            folder_entry.bind("<1>", on_click)

        Label(top, text=_("Mailbox name")).grid(row=0, column=0, sticky="e",
                                                pady=(10, 4), padx=(10, 1))
        Label(top, text=_("IMAP server")).grid(row=1, column=0, sticky="e",
                                               pady=4, padx=(10, 1))
        Label(top, text=_("Login")).grid(row=2, column=0, sticky="e",
                                         pady=4, padx=(10, 1))
        Label(top, text=_("Password")).grid(row=3, column=0, sticky="e",
                                            pady=4, padx=(10, 1))
        Label(top, text=_("Folder to check")).grid(row=4, column=0, sticky="e",
                                                   pady=4, padx=(10, 1))
        name_entry.grid(row=0, column=1, sticky="w", pady=4, padx=(1, 10))
        server_entry.grid(row=1, column=1, sticky="w", pady=4, padx=(1, 10))
        login_entry.grid(row=2, column=1, sticky="w", pady=4, padx=(1, 10))
        password_entry.grid(row=3, column=1, sticky="w", pady=4, padx=(1, 10))
        folder_entry.grid(row=4, column=1, sticky="w", pady=4, padx=(1, 10))
        frame = Frame(top)
        frame.grid(row=5, columnspan=2, pady=(0, 6))
        Button(frame, text="Ok", command=save).grid(row=0, column=0,
                                                    padx=(10, 4), pady=4)
        Button(frame, text=_("Cancel"), command=top.destroy).grid(row=0,
                                                                  column=1,
                                                                  pady=4,
                                                                  padx=(10, 4))
        top.grab_set()
        name_entry.bind("<Key-Return>", save)
        server_entry.bind("<Key-Return>", save)
        login_entry.bind("<Key-Return>", save)
        password_entry.bind("<Key-Return>", save)
        folder_entry.bind("<Key-Return>", save)
        name_entry.focus_set()


class EditMailbox(Toplevel):
    """GUI to add or modify a mailbox login information."""

    def __init__(self, master, pwd, mailbox=''):
        Toplevel.__init__(self, master, class_="CheckMails")
        self.title(_("Login information"))
        self.resizable(False, False)

        self.mailbox = mailbox
        self.name = ''
        self.pwd = pwd

        self.name_entry = Entry(self, justify='center', width=32)
        self.server_entry = Entry(self, justify='center', width=32)
        self.login_entry = Entry(self, justify='center', width=32)
        self.password_entry = Entry(self, show='*', justify='center', width=32)
        self.folder_entry = Entry(self, justify='center', width=32)

        if mailbox:
            self.name_entry.insert(0, mailbox)
            server, login, password, folder = decrypt(mailbox, self.pwd)
            if server is None:
                self.destroy()
                master.del_mailbox(mailbox)
                return
            self.server_entry.insert(0, server)
            self.login_entry.insert(0, login)
            self.password_entry.insert(0, password)
            self.folder_entry.insert(0, folder)
        else:
            self.name_entry.insert(0, "Mailbox name")
            self.server_entry.insert(0, "IMAP.mailbox.com")
            self.login_entry.insert(0, "myaddress@mailbox.com")
            self.folder_entry.insert(0, "inbox")
            self.name_entry.bind("<1>", self.on_click)
            self.server_entry.bind("<1>", self.on_click)
            self.login_entry.bind("<1>", self.on_click)
            self.password_entry.bind("<1>", self.on_click)
            self.folder_entry.bind("<1>", self.on_click)

        Label(self, text=_("Mailbox name")).grid(row=0, column=0, sticky="e",
                                                 pady=(10, 4), padx=(10, 1))
        Label(self, text=_("IMAP server")).grid(row=1, column=0, sticky="e",
                                                pady=4, padx=(10, 1))
        Label(self, text=_("Login")).grid(row=2, column=0, sticky="e",
                                          pady=4, padx=(10, 1))
        Label(self, text=_("Password")).grid(row=3, column=0, sticky="e",
                                             pady=4, padx=(10, 1))
        Label(self, text=_("Folder to check")).grid(row=4, column=0, sticky="e",
                                                    pady=4, padx=(10, 1))
        self.name_entry.grid(row=0, column=1, sticky="w", pady=4, padx=(1, 10))
        self.server_entry.grid(row=1, column=1, sticky="w", pady=4, padx=(1, 10))
        self.login_entry.grid(row=2, column=1, sticky="w", pady=4, padx=(1, 10))
        self.password_entry.grid(row=3, column=1, sticky="w", pady=4, padx=(1, 10))
        self.folder_entry.grid(row=4, column=1, sticky="w", pady=4, padx=(1, 10))
        frame = Frame(self)
        frame.grid(row=5, columnspan=2, pady=(0, 6))
        Button(frame, text="Ok", command=self.save).grid(row=0, column=0,
                                                         padx=(10, 4), pady=4)
        Button(frame, text=_("Cancel"), command=self.destroy).grid(row=0,
                                                                   column=1,
                                                                   pady=4,
                                                                   padx=(10, 4))
        self.name_entry.bind("<Key-Return>", self.save)
        self.server_entry.bind("<Key-Return>", self.save)
        self.login_entry.bind("<Key-Return>", self.save)
        self.password_entry.bind("<Key-Return>", self.save)
        self.folder_entry.bind("<Key-Return>", self.save)
        self.name_entry.focus_set()
        self.wait_visibility()
        self.grab_set()

    def on_click(self, event):
        event.widget.focus_set()
        event.widget.selection_range(0, 'end')
        event.widget.unbind('<1>')
        return "break"

    def save(self, event=None):
        self.name = name = self.name_entry.get().strip()
        if name != self.mailbox:
            # change name of mailbox
            os.remove(os.path.join(LOCAL_PATH, self.mailbox))

            active = CONFIG.get("Mailboxes", "active").split(", ")
            inactive = CONFIG.get("Mailboxes", "inactive").split(", ")
            while "" in active:
                active.remove("")
            while "" in inactive:
                inactive.remove("")
            if self.mailbox in active:
                active.remove(self.mailbox)
                active.append(name)
            elif self.mailbox in inactive:
                inactive.remove(self.mailbox)
                inactive.append(name)
            CONFIG.set("Mailboxes", "active", ", ".join(active))
            CONFIG.set("Mailboxes", "inactive", ", ".join(inactive))
            save_config()

        encrypt(name, self.pwd, self.server_entry.get().strip(),
                self.login_entry.get().strip(), self.password_entry.get().strip(),
                self.folder_entry.get().strip())

        self.destroy()
