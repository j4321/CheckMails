#! /usr/bin/python3
# -*- coding:Utf-8 -*-
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


Check for updates
"""


import re
import logging
from subprocess import run
from threading import Thread
from urllib import request, error
from html.parser import HTMLParser
from webbrowser import open as webOpen
from tkinter import Toplevel, PhotoImage
from tkinter.ttk import Label, Button, Frame, Checkbutton
from checkmailslib.constants import VERSION, CONFIG, save_config, IM_QUESTION_DATA, IMAGE2


class VersionParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.version = ""

    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        res = re.match(r"^checkmails-[0-9]+\.[0-9]+\.[0-9]+", data)
        if res:
            self.version = res.group().split("-")[-1]

    def feed(self, data):
        self.version = ""
        HTMLParser.feed(self, data)
        return self.version


class UpdateChecker(Toplevel):

    version_parser = VersionParser()

    def __init__(self, master, notify=False):
        Toplevel.__init__(self, master)
        logging.info('Checking for updates')
        self.title(_("Update"))
        self.withdraw()
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.quit)

        self.notify = notify

        self.img = PhotoImage(data=IM_QUESTION_DATA, master=self)

        frame = Frame(self)
        frame.grid(row=0, columnspan=2, sticky="ewsn")
        Label(frame, image=self.img).pack(side="left", padx=(10, 4), pady=(10, 4))
        Label(frame,
              text=_("A new version of CheckMails is available.\
\nDo you want to download it?"),
              font="TkDefaultFont 10 bold",
              wraplength=335).pack(side="left", padx=(4, 10), pady=(10, 4))

        self.b1 = Button(self, text=_("Yes"), command=self.download)
        self.b1.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        Button(self, text=_("No"), command=self.quit).grid(row=1, column=1,
                                                              padx=10, pady=10,
                                                              sticky="w")
        self.ch = Checkbutton(self, text=_("Check for updates on startup."))
        if CONFIG.getboolean("General", "check_update"):
            self.ch.state(("selected", ))
        self.ch.grid(row=2, columnspan=2, sticky='w')
        self.update = None

        self.thread = Thread(target=self.update_available, daemon=True)
        self.thread.start()
        self.after(1000, self.check_update)

    def check_update(self):
        if self.update is None:
            self.after(1000, self.check_update)
        elif self.update:
            self.deiconify()
            self.grab_set()
            self.lift()
            self.b1.focus_set()
        else:
            if self.notify:
                run(["notify-send", "-i", IMAGE2, _("Update"), _("Checkmails is up-to-date.")])
            logging.info("Checkmails is up-to-date")
            self.destroy()

    def quit(self):
        CONFIG.set("General", "check_update", str("selected" in self.ch.state()))
        save_config()
        self.destroy()

    def download(self):
        webOpen("https://sourceforge.net/projects/checkmails/files")
        self.quit()

    def update_available(self):
        """
        Check for updates online, return True if an update is available, False
        otherwise (and if there is no Internet connection).
        """
        try:
            with request.urlopen('https://sourceforge.net/projects/checkmails') as page:
                latest_version = self.version_parser.feed(page.read().decode())
            self.update = latest_version > VERSION
        except error.URLError as e:
            if e.reason.errno == -2:
                # no Internet connection
                self.update = False
            elif e.reason.errno == 104:
                # connection timed out
               self.update_available()
            else:
                raise e
