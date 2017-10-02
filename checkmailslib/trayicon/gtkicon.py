#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
CheckMails - System tray unread mail checker
Copyright 2016 Juliette Monsel <j_4321@protonmail.com>

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


System tray icon using Gtk 3.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APPIND_SUPPORT = 1
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except ValueError:
    APPIND_SUPPORT = 0


class TrayIcon:
    """Gtk system tray icon."""
    def __init__(self, icon, appid="Checkmails"):
        self.menu = Gtk.Menu()
        self.menu_items = []

        if APPIND_SUPPORT == 1:
            self.ind = AppIndicator3.Indicator.new(
                appid, icon, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.ind.set_menu(self.menu)
            self.change_icon = self._change_icon_appind
        else:
            self.ind = Gtk.StatusIcon()
            self.ind.set_from_file(icon)
            self.ind.connect('popup-menu', self._on_popup_menu)
            self.change_icon = self._change_icon_fallback

    def _on_popup_menu(self, icon, button, time):
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, time)

    def add_menu_item(self, label="", command=None):
        item = Gtk.MenuItem(label=label)
        self.menu.append(item)
        self.menu_items.append(item)
        if command is not None:
            item.connect("activate", lambda *args: command())
        item.show()

    def add_menu_separator(self):
        sep = Gtk.SeparatorMenuItem()
        self.menu.append(sep)
        self.menu_items.append(sep)
        sep.show()

    def _change_icon_appind(self, icon, desc):
        self.ind.set_icon_full(icon, desc)

    def _change_icon_fallback(self, icon, desc):
        self.ind.set_from_file(icon)

    def loop(self, tk_window):
        """Update Gtk GUI inside tkinter mainloop."""
        while Gtk.events_pending():
            Gtk.main_iteration()
        tk_window.loop_id = tk_window.after(10, self.loop, tk_window)

    def get_item_label(self, item):
        return self.menu_items[item].get_label()

    def set_item_label(self, item, label):
        self.menu_items[item].set_label(label)

    def disable_item(self, item):
        self.menu_items[item].set_sensitive(False)

    def enable_item(self, item):
        self.menu_items[item].set_sensitive(True)

    def bind_left_click(self, command):
        if not APPIND_SUPPORT:
            self.ind.connect('activate', lambda *args: command())
