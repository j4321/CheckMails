#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

Configuration dialog
"""

from checkmailslib.constants import CONFIG, LANG, save_config
from tkinter import Toplevel, Menu, StringVar
from tkinter.messagebox import showinfo
from tkinter.ttk import Label, Button, Entry, Menubutton, Frame
_ = LANG.gettext

class Config(Toplevel):
    """ Configuration dialog to set times and language. """

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title(_("Preferences"))

        # validation of the entries : only numbers are allowed
        self._validate_entry_nb = self.register(self.validate_entry_nb)

        Label(self, text=_("Time between two checks")).grid(row=0, column=0, padx=(10,4), pady=(10,4))
        Label(self, text=_("Maximum time allowed for login or check\n(then the connection is reset)")).grid(row=1, column=0, padx=(10,4), pady=4)
        self.time_entry = Entry(self, width=5, justify="center",
                                validate="key",
                                validatecommand=(self._validate_entry_nb, "%P"))
        self.time_entry.grid(row=0, column=1, padx=(4,0), pady=(10,4))
        self.time_entry.insert(0, "%g" % (CONFIG.getint("General", "time")/60000))
        self.timeout_entry = Entry(self, width=5, justify="center",
                                   validate="key",
                                   validatecommand=(self._validate_entry_nb, "%P"))
        self.timeout_entry.grid(row=1, column=1, padx=(4,0), pady=4)
        self.timeout_entry.insert(0, "%g" % (CONFIG.getint("General", "timeout")/60000))
        Label(self, text="min").grid(row=0, column=2, padx=(0,10), pady=(10,4))
        Label(self, text="min").grid(row=1, column=2, padx=(0,10), pady=4)

        frame = Frame(self)
        frame.grid(row=2,columnspan=3, padx=6, pady=(0,6))
        Label(frame, text=_("Language")).grid(row=0, column=0, padx=4, pady=4)
        self.lang = StringVar(self, CONFIG.get("General","language"))
        menu_lang = Menu(frame, tearoff=False)
        Menubutton(frame, menu=menu_lang,
                   textvariable=self.lang).grid(row=0, column=1, padx=4, pady=4)
        menu_lang.add_radiobutton(label="English", value="English",
                                  variable=self.lang, command=self.translate)
        menu_lang.add_radiobutton(label="Français", value="Français",
                                  variable=self.lang, command=self.translate)
        Button(frame, text="Ok", command=self.ok).grid(row=1, column=0, padx=4, pady=4)
        Button(frame, text=_("Cancel"), command=self.destroy).grid(row=1, column=1,
                                                                   padx=4, pady=4)

    def ok(self):
        time = float(self.time_entry.get())*60000
        timeout = float(self.timeout_entry.get())*60000
        CONFIG.set("General", "time", "%i" % time)
        CONFIG.set("General", "timeout", "%i" % timeout)
        CONFIG.set("General", "language", self.lang.get().lower()[:2])
        save_config()
        self.destroy()

    def translate(self):
        showinfo("Information",
                 _("The language setting will take effect after restarting the application"),
                parent=self)

    @staticmethod
    def validate_entry_nb(P):
        """ Allow only to enter numbers"""
        parts = P.split(".")
        b = len(parts) < 3 and P != "."
        for p in parts:
            b = b and (p == "" or p.isdigit())
        return b

