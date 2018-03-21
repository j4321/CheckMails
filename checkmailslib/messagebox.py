#! /usr/bin/python3
# -*- coding:Utf-8 -*-
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

Custom messagebox
"""

from tkinter import Toplevel
from tkinter.ttk import Button, Label, Frame
from checkmailslib.constants import IM_ERROR, PhotoImage


class FailedAuthBox(Toplevel):
    """Message box to ask what to do in case of authentication failure."""

    def __init__(self, master, box):
        """Create message box."""
        Toplevel.__init__(self, master, class_="CheckMails")
        self.title(_("Error"))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.im_error = PhotoImage(master=self, file=IM_ERROR)

        self._result = ''

        Label(self, image=self.im_error).grid(row=0, column=0, sticky='e', padx=4, pady=4)
        msg = _("Incorrect login or password for %(mailbox)s") % {"mailbox": box}
        Label(self, text=msg, wrap=200).grid(row=0, column=1, sticky='ew', padx=4, pady=4)
        frame_buttons = Frame(self)
        frame_buttons.grid(row=1, columnspan=2, sticky='ew')
        Button(frame_buttons, command=self.deactivate,
               text=_('Deactivate mailbox')).pack(side='left', padx=4, pady=4, fill='x')
        Button(frame_buttons, command=self.correct_login,
               text=_('Correct login')).pack(side='right', padx=4, pady=4, fill='x')
        self.wait_visibility()
        self.grab_set()

    def deactivate(self):
        self._result = 'deactivate'
        self.destroy()

    def correct_login(self):
        self._result = 'correct'
        self.destroy()

    def get_result(self):
        return self._result


def show_failed_auth_msg(master, box):
    box = FailedAuthBox(master, box)
    box.wait_window(box)
    return box.get_result()
