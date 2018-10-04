CheckMails - System tray unread mail checker
=============================================
|Release| |Linux| |License|

CheckMails periodically looks for unread mails and displays the total number
of unread mails in the system tray icon. Several mailboxes can be configured.
The number of unread mails for each mailbox is detailed in a notification
that appears when clicking on the icon and after a check. This application
supports only the IMAP protocol with SSL encryption. The connection information
for each mailbox is stored in an encrypted file using a master password.

CheckMails is designed for Linux. It is written in Python 3 and relies mostly
upon Tk GUI toolkit.


Install
-------

- Archlinux

    CheckMails is available on `AUR <https://aur.archlinux.org/packages/checkmails>`__.

- Ubuntu

    CheckMails is available in the PPA `ppa:j-4321-i/ppa <https://launchpad.net/~j-4321-i/+archive/ubuntu/ppa>`__.

    ::

        $ sudo add-apt-repository ppa:j-4321-i/ppa
        $ sudo apt-get update
        $ sudo apt-get install checkmails

- Source code

    First, install the missing dependencies among:
    
     - Tkinter (Python wrapper for Tk)
     - libnotify and a notification server if your desktop environment does not provide one.
       (see https://wiki.archlinux.org/index.php/Desktop_notifications for more details)
     - PyCryptodome (https://pypi.python.org/pypi/pycryptodome) or PyCrypto (https://pypi.python.org/pypi/pycrypto)
     - Pillow https://pypi.python.org/pypi/Pillow

    You also need to have at least one of the following GUI toolkits for the system tray icon:
    
     - Tktray https://code.google.com/archive/p/tktray/downloads
     - PyGTK http://www.pygtk.org/downloads.html
     - PyQt5, PyQt4 or PySide


    For instance, in Ubuntu/Debian you will need to install the following packages:
    python3-tk, tk-tktray (or python3-gi or python3-pyqt5), 
    libnotify and the notification server of your choice, python3-crypto, 
    python3-pil

    In Archlinux, you will need to install the following packages:
    tk, tktray (`AUR <https://aur.archlinux.org/packages/tktray>`__) (or python-gobject or python-pyqt5), 
    libnotify and the notification server of your choice,
    python-pycryptodome, python-pillow

    Then install the application:
    
    ::
    
        $ sudo python3 setup.py install


You can now launch it from *Menu > Network > CheckMails*. You can launch
it from the command line with ``checkmails``. In this last case, you will see
the messages printed every time a process is lauched or finished and when
an error is encountered. Therefore you can check that everything works fine.

Troubleshooting
---------------

Several gui toolkits are available to display the system tray icon, so if the
icon does not behave properly, try to change toolkit, they are not all fully
compatible with every desktop environment.

If there is a problem with the font of the number of unread mails, try to change
the font from the settings.

If you encounter bugs or if you have suggestions, please open an issue on
`GitHub <https://github.com/j4321/CheckMails/issues>`__ or write me an email
at <j_4321@protonmail.com>.


.. |Release| image:: https://badge.fury.io/gh/j4321%2FCheckMails.svg
    :alt: Latest Release
    :target: https://github.com/j4321/CheckMails/releases
.. |Linux| image:: https://img.shields.io/badge/platform-Linux-blue.svg
    :alt: Linux
.. |License| image:: https://img.shields.io/github/license/j4321/CheckMails.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.en.html

