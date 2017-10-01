#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CheckMails - System tray unread mail checker
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

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
from re import search
from os.path import expanduser, join
from os import listdir
from checkmailslib.constants import CONFIG, save_config, IMAGE, PREV
from PIL import Image, ImageDraw, ImageFont
from tkinter import Toplevel, Menu, StringVar, PhotoImage
from tkinter.messagebox import showinfo
from tkinter.ttk import Label, Button, Entry, Menubutton, Frame, Style, Combobox


class Config(Toplevel):
    """ Configuration dialog to set times and language. """

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title(_("Preferences"))

        style = Style(self)
        style.map("TCombobox",
                  fieldbackground=[('readonly', 'white')],
                  selectbackground=[('readonly', 'white')],
                  selectforeground=[('readonly', 'black')])

        # validation of the entries : only numbers are allowed
        self._validate_entry_nb = self.register(self.validate_entry_nb)

        # --- Times
        Label(self,
              text=_("Time between two checks")).grid(row=0, column=0,
                                                      padx=(10, 4), pady=(10, 4),
                                                      sticky="e")
        Label(self, justify="right",
              text=_("Maximum time allowed for login or check\n\
(then the connection is reset)")).grid(row=1, column=0, padx=(10, 4), pady=4, sticky="e")
        self.time_entry = Entry(self, width=5, justify="center",
                                validate="key",
                                validatecommand=(self._validate_entry_nb, "%P"))
        self.time_entry.grid(row=0, column=1, padx=(4, 0), pady=(10, 4))
        self.time_entry.insert(0, "%g" % (CONFIG.getint("General", "time") / 60000))
        self.timeout_entry = Entry(self, width=5, justify="center",
                                   validate="key",
                                   validatecommand=(self._validate_entry_nb, "%P"))
        self.timeout_entry.grid(row=1, column=1, padx=(4, 0), pady=4)
        self.timeout_entry.insert(0, "%g" % (CONFIG.getint("General", "timeout") / 60000))
        Label(self, text="min").grid(row=0, column=2, padx=(0, 10), pady=(10, 4))
        Label(self, text="min").grid(row=1, column=2, padx=(0, 10), pady=4)

        frame = Frame(self)
        frame.grid(row=2, columnspan=3, padx=6, pady=(0, 6))

        # --- Language
        Label(frame, text=_("Language")).grid(row=0, column=0,
                                              padx=8, pady=4, sticky="e")
        lang = {"fr": "Français", "en": "English"}
        self.lang = StringVar(self, lang[CONFIG.get("General", "language")])
        menu_lang = Menu(frame, tearoff=False)
        Menubutton(frame, menu=menu_lang, width=9,
                   textvariable=self.lang).grid(row=0, column=1,
                                                padx=8, pady=4, sticky="w")
        menu_lang.add_radiobutton(label="English", value="English",
                                  variable=self.lang, command=self.translate)
        menu_lang.add_radiobutton(label="Français", value="Français",
                                  variable=self.lang, command=self.translate)
        # --- Font
        local_path = join(expanduser("~"), ".fonts")
        sys_path = "/usr/share/fonts/TTF"
        try:
            local_fonts = listdir(local_path)
        except FileNotFoundError:
            local_fonts= []
        self.ttf_fonts = {f.split(".")[0]: join(local_path, f)
                          for f in local_fonts if search(r".(ttf|TTF)$", f)}
        self.ttf_fonts.update({f.split(".")[0]: join(sys_path, f) for f in listdir(sys_path)})
        w = max([len(f) for f in self.ttf_fonts])
        self.fonts = list(self.ttf_fonts)
        self.fonts.sort()
        self.font = Combobox(frame, values=self.fonts, width=(w * 2) // 3,
                             exportselection=False, state="readonly")
        current_font = CONFIG.get("General", "font")
        if current_font in self.fonts:
            i = self.fonts.index(current_font)
        else:
            i = 0
        self.font.current(i)
        self.img_prev = PhotoImage(master=self, file=IMAGE)
        Label(frame, text=_("Font")).grid(row=1, column=0,
                                          padx=8, pady=4, sticky="e")
        self.font.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        self.prev = Label(frame, image=self.img_prev)
        self.prev.grid(row=1, column=2, padx=8, pady=4)
        self.update_preview()
        self.font.bind('<<ComboboxSelected>>', self.update_preview)

        # --- Ok/Cancel
        frame_button = Frame(self)
        frame_button.grid(row=3, columnspan=3, padx=6, pady=(0, 6))
        Button(frame_button, text="Ok",
               command=self.ok).grid(row=2, column=0, padx=8, pady=4)
        Button(frame_button, text=_("Cancel"),
               command=self.destroy).grid(row=2, column=1, padx=4, pady=4)

    def update_preview(self, event=None):
        nb = "0"
        im = Image.open(IMAGE)
        draw = ImageDraw.Draw(im)
        font_name = self.font.get()
        font_path = self.ttf_fonts[font_name]
        try:
            font = ImageFont.truetype(font_path, 10)
            draw.text((6 // len(nb), 4), nb, fill=(255, 0, 0), font=font)
        except OSError:
            draw.text((6 // len(nb), 4), nb, fill=(255, 0, 0))
        im.save(PREV)
        self.img_prev.configure(file=PREV)
        self.prev.configure(image=self.img_prev)
        self.prev.update_idletasks()

    def ok(self):
        time = float(self.time_entry.get()) * 60000
        timeout = float(self.timeout_entry.get()) * 60000
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
