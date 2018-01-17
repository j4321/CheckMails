#! /usr/bin/python3
# -*- coding:Utf-8 -*-


from setuptools import setup

import os

images = [os.path.join("checkmailslib/images/", img) for img in os.listdir("checkmailslib/images/")]
data_files = [("/usr/share/applications", ["checkmails.desktop"]),
              ("/usr/share/checkmails/images/", images),
              ("/usr/share/doc/checkmails/", ["README.rst", "changelog"]),
              ("/usr/share/man/man1", ["checkmails.1.gz"]),
              ("/usr/share/locale/en_US/LC_MESSAGES/", ["checkmailslib/locale/en_US/LC_MESSAGES/checkmails.mo"]),
              ("/usr/share/locale/fr_FR/LC_MESSAGES/", ["checkmailslib/locale/fr_FR/LC_MESSAGES/checkmails.mo"]),
              ("/usr/share/pixmaps", ["checkmails.svg"])]

with open("checkmailslib/version.py") as file:
    exec(file.read())

setup(name="checkmails",
      version=__version__,
      description="System tray unread mail checker",
      author="Juliette Monsel",
      author_email="j_4321@protonmail.com",
      license="GPLv3",
      url="https://sourceforge.net/projects/checkmails",
      packages=['checkmailslib', 'checkmailslib.trayicon'],
      package_data={'checkmailslib': ["packages.tcl"]},
      scripts=["checkmails"],
      data_files=data_files,
      classifiers=[
           'Development Status :: 5 - Production/Stable',
           'Environment :: X11 Applications',
           'Intended Audience :: End Users/Desktop',
           'Topic :: Communications :: Email',
           'Topic :: Office/Business',
           'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
           'Programming Language :: Python :: 3',
           'Programming Language :: Python :: 3.5',
           'Programming Language :: Python :: 3.6',
           'Natural Language :: English',
           'Natural Language :: French',
           'Operating System :: POSIX :: Linux',
      ],
      long_description="""
CheckMails periodically looks for unread mails and displays the total number
of unread mails in the system tray icon. Several mailboxes can be configured.
The number of unread mails for each mailbox is detailed in a notification
that appears when clicking on the icon and after a check. This application
supports only IMAP protocol with SSL encryption. The connection information
for each mailbox is stored in an encrypted file using a master password.
""",
      requires=["tkinter", "sys", "os", "re", "locale", "gettext",
                "crypt", "Crypto", 'hashlib', 'configparser', "feedparser",
                'imaplib', 'socket', 'threading', 'subprocess'])
