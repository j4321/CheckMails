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
from os import listdir, remove
from checkmailslib.constants import CONFIG, save_config, IMAGE, TTF_FONTS, TOOLKITS, FONTSIZE
from PIL import Image, ImageDraw, ImageFont
from tkinter import Toplevel, Menu, StringVar, PhotoImage
from tkinter.messagebox import showinfo
from tkinter.ttk import Label, Button, Entry, Menubutton, Frame, Style, Combobox
import tempfile


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
        # --- gui toolkit
        Label(frame,
              text=_("GUI Toolkit for the system tray icon")).grid(row=1, column=0,
                                                                   padx=8, pady=4,
                                                                   sticky="e")
        self.gui = StringVar(self, CONFIG.get("General", "trayicon").capitalize())
        menu_gui = Menu(frame, tearoff=False)
        Menubutton(frame, menu=menu_gui, width=9,
                   textvariable=self.gui).grid(row=1, column=1,
                                               padx=8, pady=4, sticky="w")
        for toolkit, b in TOOLKITS.items():
            if b:
                menu_gui.add_radiobutton(label=toolkit.capitalize(),
                                         value=toolkit.capitalize(),
                                         variable=self.gui,
                                         command=self.change_gui)
        # --- Font
        self.preview_path = tempfile.mktemp(".png", "checkmails_preview")
        w = max([len(f) for f in TTF_FONTS])
        self.fonts = list(TTF_FONTS)
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
        Label(frame, text=_("Font")).grid(row=2, column=0,
                                          padx=8, pady=4, sticky="e")
        self.font.grid(row=2, column=1, padx=8, pady=4, sticky="w")
        self.prev = Label(frame, image=self.img_prev)
        self.prev.grid(row=2, column=2, padx=8, pady=4)
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
        font_path = TTF_FONTS[font_name]
        W, H = im.size
        try:
            font = ImageFont.truetype(font_path, FONTSIZE)
            w, h = draw.textsize(nb, font=font)
            draw.text(((W - w) / 2, (H - h) / 2), nb, fill=(255, 0, 0),
                      font=font)
        except OSError:
            w, h = draw.textsize(nb)
            draw.text(((W - w) / 2, (H - h) / 2), nb, fill=(255, 0, 0))
        if W > 48:
            im.resize((48, 48), Image.ANTIALIAS).save(self.preview_path)
        else:
            im.save(self.preview_path)
        self.img_prev.configure(file=self.preview_path)
        self.prev.configure(image=self.img_prev)
        self.prev.update_idletasks()

    def ok(self):
        time = float(self.time_entry.get()) * 60000
        timeout = float(self.timeout_entry.get()) * 60000
        CONFIG.set("General", "time", "%i" % time)
        CONFIG.set("General", "timeout", "%i" % timeout)
        CONFIG.set("General", "language", self.lang.get().lower()[:2])
        CONFIG.set("General", "font", self.font.get())
        CONFIG.set("General", "trayicon", self.gui.get().lower())
        save_config()
        self.destroy()

    def translate(self):
        showinfo("Information",
                 _("The language setting will take effect after restarting the application"),
                 parent=self)

    def change_gui(self):
        showinfo("Information",
                 _("The GUI Toolkit setting will take effect after restarting the application"),
                 parent=self)

    @staticmethod
    def validate_entry_nb(P):
        """ Allow only to enter numbers"""
        parts = P.split(".")
        b = len(parts) < 3 and P != "."
        for p in parts:
            b = b and (p == "" or p.isdigit())
        return b

    def destroy(self):
        remove(self.preview_path)
        Toplevel.destroy(self)
