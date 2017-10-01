#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  1 17:09:01 2017

@author: tux
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class TrayIcon:
    """Gtk system tray icon."""
    def __init__(self, appid, icon):
        self.menu = Gtk.Menu()
        self.menu_items = []

        APPIND_SUPPORT = 1
        try:
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3
        except ImportError:
            APPIND_SUPPORT = 0

        if APPIND_SUPPORT == 1:
            self.ind = AppIndicator3.Indicator.new(
                appid, icon, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.ind.set_menu(self.menu)
        else:
            self.ind = Gtk.StatusIcon()
            self.ind.set_from_file(icon)
            self.ind.connect('popup-menu', self.on_popup_menu)

    def on_popup_menu(self, icon, button, time):
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

    def change_icon(self, icon):
        self.ind.set_icon(icon)


def gtk_loop(tk_window):
    """Update Gtk GUI inside tkinter mainloop."""
    while Gtk.events_pending():
        Gtk.main_iteration()
    tk_window.gtk_loop_id = tk_window.after(10, gtk_loop, tk_window)
