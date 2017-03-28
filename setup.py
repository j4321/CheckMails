#! /usr/bin/python3
# -*- coding:Utf-8 -*-

try:
    from setuptools import setup
except:
    from distutils.core import setup

#  files = ["images/*", "locale/en_US/LC_MESSAGES/*", "locale/fr_FR/LC_MESSAGES/*"]
files = ["images/*" , "locale/en_US/LC_MESSAGES/*", "locale/fr_FR/LC_MESSAGES/*"]
data_files = [("share/applications", ["checkmails.desktop"]),
              ("share/pixmaps", ["checkmails.svg"])]

setup(name = "checkmails",
      version = "1.1.1",
      description = "System tray unread mail checker",
      author = "Juliette Monsel",
      author_email = "j_4321@protonmail.fr",
      license = "GNU General Public License v3",
      #Name the folder where your packages live:
      #(If you have other packages (dirs) or modules (py files) then
      #put them into the package directory - they will be found
      #recursively.)
      packages = ['checkmailslib'],
      #'package' package must contain files (see list above)
      #I called the package 'package' thus cleverly confusing the whole issue...
      #This dict maps the package name =to=> directories
      #It says, package *needs* these files.
      package_data = {'checkmailslib' : files },
      #'runner' is in the root.
      scripts = ["checkmails"],
      data_files = data_files,
      long_description =
"""
CheckMails periodically looks for unread mails and displays the total number
of unread mails in the system tray icon. Several mailboxes can be configured.
The number of unread mails for each mailbox is detailed in a notification
that appears when clicking on the icon and after a check. This application
supports only IMAP protocol with SSL encryption. The connection information
for each mailbox is stored in an encrypted file using a master password.
""",
      requires = ["tkinter", "sys", "os", "re",  "locale", "gettext", "crypt", "Crypto", 'hashlib', 'configparser', 'imaplib', 'socket', 'threading',
'subprocess']
)


