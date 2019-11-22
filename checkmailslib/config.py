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

Configuration dialog
"""
from os import remove
from tkinter import Toplevel, Menu, StringVar
from tkinter.messagebox import showinfo
from tkinter.ttk import Label, Button, Entry, Menubutton, Frame, Style, \
    Combobox, Checkbutton
import tempfile

from PIL import Image, ImageDraw, ImageFont

from checkmailslib.constants import CONFIG, save_config, IMAGE, \
    TTF_FONTS, TOOLKITS, FONTSIZE, PhotoImage


class Config(Toplevel):
    """ Configuration dialog to set times and language. """

    def __init__(self, master):
        Toplevel.__init__(self, master, class_="CheckMails", pady=4)
        self.title(_("Preferences"))

        style = Style(self)
        style.map("TCombobox",
                  fieldbackground=[('readonly', 'white')],
                  selectbackground=[('readonly', 'white')],
                  selectforeground=[('readonly', 'black')],
                  foreground=[('readonly', 'black')])

        # validation of the entries : only numbers are allowed
        self._validate_entry_nb = self.register(self.validate_entry_nb)

        # --- Times
        frame_times = Frame(self)
        self.time_entry = Entry(frame_times, width=5, justify="center",
                                validate="key",
                                validatecommand=(self._validate_entry_nb, "%P"))
        self.time_entry.insert(0, "%g" % (CONFIG.getint("General", "time") / 60000))
        self.timeout_entry = Entry(frame_times, width=5, justify="center",
                                   validate="key",
                                   validatecommand=(self._validate_entry_nb, "%P"))
        self.timeout_entry.insert(0, "%g" % (CONFIG.getint("General", "timeout") / 60000))

        Label(frame_times,
              text=_("Time between two checks")).grid(row=0, column=0,
                                                      padx=4, pady=4,
                                                      sticky="e")
        Label(frame_times,
              text=_("Maximum time allowed for login or check\n(then the connection is reset)"),
              justify="right").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.time_entry.grid(row=0, column=1, padx=0, pady=4)
        self.timeout_entry.grid(row=1, column=1, padx=0, pady=4)
        Label(frame_times, text="min").grid(sticky='w', row=0, column=2, padx=0, pady=4)
        Label(frame_times, text="min").grid(sticky='w', row=1, column=2, padx=0, pady=4)

        frame_GUI = Frame(self)
        # --- Language
        Label(frame_GUI, text=_("Language")).grid(row=0, column=0,
                                                  padx=4, pady=4, sticky="e")
        lang = {"fr": "Français", "en": "English"}
        self.lang = StringVar(self, lang[CONFIG.get("General", "language")])
        menu_lang = Menu(frame_GUI, tearoff=False)
        Menubutton(frame_GUI, menu=menu_lang, width=9,
                   textvariable=self.lang).grid(row=0, column=1,
                                                padx=4, pady=4, sticky="w")
        menu_lang.add_radiobutton(label="English", value="English",
                                  variable=self.lang, command=self.translate)
        menu_lang.add_radiobutton(label="Français", value="Français",
                                  variable=self.lang, command=self.translate)
        # --- gui toolkit
        Label(frame_GUI,
              text=_("GUI Toolkit for the system tray icon")).grid(row=1, column=0,
                                                                   padx=4, pady=4,
                                                                   sticky="e")
        self.gui = StringVar(self, CONFIG.get("General", "trayicon").capitalize())
        menu_gui = Menu(frame_GUI, tearoff=False)
        Menubutton(frame_GUI, menu=menu_gui, width=9,
                   textvariable=self.gui).grid(row=1, column=1,
                                               padx=4, pady=4, sticky="w")
        for toolkit, b in TOOLKITS.items():
            if b:
                menu_gui.add_radiobutton(label=toolkit.capitalize(),
                                         value=toolkit.capitalize(),
                                         variable=self.gui,
                                         command=self.change_gui)
        # --- Font
        frame_font = Frame(self)
        self.preview_path = tempfile.mktemp(".png", "checkmails_preview")
        w = max([len(f) for f in TTF_FONTS])
        self.fonts = sorted(TTF_FONTS)
        self.font = Combobox(frame_font, values=self.fonts, width=(w * 2) // 3,
                             exportselection=False, state="readonly")
        current_font = CONFIG.get("General", "font")
        if current_font in self.fonts:
            i = self.fonts.index(current_font)
        else:
            i = 0
        self.font.current(i)
        self.img_prev = PhotoImage(master=self, file=IMAGE)
        Label(frame_font, text=_("Font")).grid(row=2, column=0,
                                               padx=4, pady=4, sticky="e")
        self.font.grid(row=2, column=1, padx=4, pady=4, sticky="w")
        self.prev = Label(frame_font, image=self.img_prev)
        self.prev.grid(row=2, column=2, padx=4, pady=4)
        self.update_preview()
        self.font.bind('<<ComboboxSelected>>', self.update_preview)
        self.font.bind_class("ComboboxListbox", '<KeyPress>', self.key_nav)

        # --- notifications
        frame_notif = Frame(self)
        self.notify_nb_unread = Checkbutton(frame_notif, text=_('Notifications for number of unread emails'))
        if CONFIG.getboolean('General', 'notify_nb_unread', fallback=True):
            self.notify_nb_unread.state(('selected', '!alternate'))
        else:
            self.notify_nb_unread.state(('!selected', '!alternate'))
        self.notify_nb_unread.grid(row=0, padx=4, pady=4, sticky='w')

        self.notify_new_unread = Checkbutton(frame_notif, text=_('Notifications for new emails displaying subject and sender'))
        if CONFIG.getboolean('General', 'notify_new_unread', fallback=True):
            self.notify_new_unread.state(('selected', '!alternate'))
        else:
            self.notify_new_unread.state(('!selected', '!alternate'))
        self.notify_new_unread.grid(row=1, padx=4, pady=4, sticky='w')

        # --- Update checks
        self.confirm_update = Checkbutton(frame_notif,
                                          text=_("Check for updates on start-up"))
        self.confirm_update.grid(row=2, padx=4, pady=4, sticky='w')
        if CONFIG.getboolean('General', 'check_update', fallback=True):
            self.confirm_update.state(('selected', '!alternate'))
        else:
            self.confirm_update.state(('!selected', '!alternate'))

        # --- Ok/Cancel
        frame_button = Frame(self)
        Button(frame_button, text="Ok",
               command=self.ok).grid(row=2, column=0, padx=8, pady=4)
        Button(frame_button, text=_("Cancel"),
               command=self.destroy).grid(row=2, column=1, padx=4, pady=4)

        # --- placement
        frame_times.grid(row=0, padx=10, pady=4, sticky='w')
        frame_GUI.grid(row=1, padx=10, pady=4, sticky='w')
        frame_font.grid(row=2, padx=10, pady=4, sticky='w')
        frame_notif.grid(row=3, padx=10, pady=4, sticky='w')
        frame_button.grid(row=4, padx=10, pady=4)

    def update_preview(self, event=None):
        self.font.selection_clear()
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

    def key_nav(self, event):
        char = event.char.upper()
        if char:
            i = 0
            n = len(self.fonts)
            while i < n and self.fonts[i] < char:
                i += 1
            if i < n:
                self.tk.eval("%s selection clear 0 end" % (event.widget))
                self.tk.eval("%s see %i" % (event.widget, i))
                self.tk.eval("%s selection set %i" % (event.widget, i))
                self.tk.eval("%s activate %i" % (event.widget, i))

    def ok(self):
        time = float(self.time_entry.get()) * 60000
        timeout = float(self.timeout_entry.get()) * 60000
        CONFIG.set("General", "time", "%i" % time)
        CONFIG.set("General", "timeout", "%i" % timeout)
        CONFIG.set("General", "language", self.lang.get().lower()[:2])
        CONFIG.set("General", "font", self.font.get())
        CONFIG.set("General", "trayicon", self.gui.get().lower())
        CONFIG.set('General', 'notify_nb_unread', str(self.notify_nb_unread.instate(('selected',))))
        CONFIG.set('General', 'notify_new_unread', str(self.notify_new_unread.instate(('selected',))))
        CONFIG.set('General', 'check_update', str(self.confirm_update.instate(('selected',))))
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
