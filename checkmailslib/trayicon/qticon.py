#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
CheckMails - System tray unread mail checker
Copyright 2016-2019 Juliette Monsel <j_4321@protonmail.com>

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


System tray icon using Qt.
"""
import sys

try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
    from PyQt5.QtGui import QIcon
except ImportError:
    try:
        from PyQt4.QtGui import QApplication, QSystemTrayIcon, QMenu, QAction, QIcon
    except ImportError:
        from PySide.QtGui import QApplication, QSystemTrayIcon, QMenu, QAction, QIcon


class TrayIcon(QApplication):

    def __init__(self, icon):
        QApplication.__init__(self, sys.argv)
        # Init QSystemTrayIcon
        self.icon = QIcon(icon)
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.icon)

        self.menu = QMenu()
        self.menu_items = []
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

    def add_menu_separator(self):
        self.menu.addSeparator()

    def add_menu_item(self, label="", command=None):
        action = QAction(label, self.tray_icon)
        action.triggered.connect(lambda *args: command())
        self.menu.addAction(action)
        self.menu_items.append(action)

    def loop(self, tk_window):
        self.processEvents()
        tk_window.loop_id = tk_window.after(10, self.loop, tk_window)

    def change_icon(self, icon, desc):
        del self.icon
        self.icon = QIcon(icon)
        self.tray_icon.setIcon(self.icon)

    def get_item_label(self, item):
        return self.menu_items[item].text()

    def set_item_label(self, item, label):
        self.menu_items[item].setText(label)

    def disable_item(self, item):
        self.menu_items[item].setDisabled(True)

    def enable_item(self, item):
        self.menu_items[item].setDisabled(False)

    def bind_left_click(self, command):

        def action(reason):
            """Execute command only on click (not when the menu is displayed)."""
            if reason == QSystemTrayIcon.Trigger:
                command()

        self.tray_icon.activated.connect(action)
