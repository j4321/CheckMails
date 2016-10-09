Checkmails - System tray unread mail checker
=============================================
Copyright 2016 Juliette Monsel <j_4321@sfr.fr>

CheckMails periodically looks for unread mails and displays the total number 
of unread mails in the system tray icon. Several mailboxes can be configured. 
The number of unread mails for each mailbox is detailed in a notification 
that appears when clicking on the icon and after a check. This application 
supports only IMAP protocol with SSL encryption. The connection information 
for each mailbox is stored in an encrypted file using a master password.

CheckMails is designed for Linux. It is written in Python 3 and relies upon 
Tk GUI toolkit. 

Install
-------

First, install the missing dependencies among:
- Tkinter (Python wrapper for Tk)
- Tktray <https://code.google.com/archive/p/tktray/downloads> 
- libnotify and a notification server if your desktop environment does not
  provide one.
  (see <https://wiki.archlinux.org/index.php/Desktop_notifications> for 
   more details)
- PyCrypto <https://pypi.python.org/pypi/pycrypto>
- Pillow <https://pypi.python.org/pypi/Pillow> 

For instance, in Ubuntu/Debian you will need to install the following packages:
python3-tk, tk-tktray, libnotify and the notification server of your choice, 
python3-crypto, python3pil

In Archlinux, you will need to install the following packages:
tk, tktray (AUR), libnotify and the notification server of your choice,
python-crypto, python-pillow

Then install the application:

::

    $ sudo python3 setup.py install

You can now launch it from `Menu > Utility > CheckMails`. You can launch
it from the command line with `checkmails`. In this last case, you will see
the messages printed every time a process is lauched or finished and when 
an error is encountered. Therefore you can check that everything works fine.

If you encounter bugs or if you have suggestions, please write me an email
at <j_4321@hotmail.fr>.

