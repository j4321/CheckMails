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


System tray icon.
"""


from checkmailslib.constants import GUI

if GUI == 'gtk':
    from checkmailslib.trayicon.gtkicon import TrayIcon
elif GUI == 'qt':
    from checkmailslib.trayicon.qticon import TrayIcon
else:
    from checkmailslib.trayicon.tkicon import TrayIcon
