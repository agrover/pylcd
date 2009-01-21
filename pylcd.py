# Copyright (C) 2002, 2003 Tobias Klausmann
# Copyright (C) 2008 Andy Grover <andy@groveronline.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# By reading this code you agree not to ridicule the author =)

__version__="0.3"
__author__="andy@groveronline.com"
__doc__="""PyLCD v%s (c) 2002, 2003 Tobias Klausman

PyLCD is a Library that interfaces with the LCDproc daemon. It abstracts the
network connection handling and provides a remap function for special
characters.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA 02111-1307, USA.

Please e-mail bugs to: %s""" % (__version__, __author__)

from exceptions import Exception
from telnetlib import Telnet

class ServerError(Exception):
    pass

PRIO_EMERG = 16
PRIO_VHIGH = 32
PRIO_HIGH = 64
PRIO_NORMAL = 128
PRIO_LOW = 192
PRIO_VLOW = 224

W_STRING   = "string"
W_HBAR     = "hbar"
W_VBAR     = "vbar"
W_ICON     = "icon"
W_TITLE    = "title"
W_SCROLLER = "scroller"
W_FRAME    = "frame"
W_NUM      = "num"

ICON_BLOCK_FILLED = "BLOCK_FILLED"
ICON_HEART_OPEN = "HEART_OPEN"
ICON_HEART_FILLED = "HEART_FILLED"
ICON_ARROW_UP = "ARROW_UP"
ICON_ARROW_DOWN = "ARROW_DOWN"
ICON_ARROW_LEFT = "ARROW_LEFT"
ICON_ARROW_RIGHT = "ARROW_RIGHT"
ICON_CHECKBOX_OFF = "CHECKBOX_OFF"
ICON_CHECKBOX_ON = "CHECKBOX_ON"
ICON_CHECKBOX_GRAY = "CHECKBOX_GRAY"
ICON_SELECTOR_AT_LEFT = "SELECTOR_AT_LEFT"
ICON_SELECTOR_AT_RIGHT = "SELECTOR_AT_RIGHT"
ICON_ELLIPSIS = "ELLIPSIS"
ICON_STOP = "STOP"
ICON_PAUSE = "PAUSE"
ICON_PLAY = "PLAY"
ICON_PLAYR = "PLAYR"
ICON_FF = "FF"
ICON_FR = "FR"
ICON_NEXT = "NEXT"
ICON_PREV = "PREV"
ICON_REC = "REC"

DIR_HORIZ = "h"
DIR_HORIZ_MARQUEE = "m"
DIR_VERT  = "v"


def _name_clean(name):
    """
    All names used as IDs can't have whitespace
    """
    return "".join(name.split())

_counter = 0
def _name_gen(obj):
    global _counter
    _counter += 1
    return obj.__class__.__name__ + str(_counter)

class Client(object):
    """
    This class opens a connection to the LCD daemon
    on the specified host and encapsulates all the
    functions of the LCDd protocol.
    """
    def __init__(self, host="localhost", port=13666):
        """
        Connect to the LCD daemon.
        """

        self.name = _name_gen(self)
        self._conn = Telnet(host,port)
        self.screens = []
        
        try:
            response = self._send_recv("hello").split()
            self.server = response[1]
            self.s_version = response[2]
            self.proto = response[4]
            self.type = response[5]
            self.d_width = int(response[7])
            self.d_height = int(response[9])
            self.c_width = int(response[11])
            self.c_height = int(response[13])

        except ValueError:
            raise ServerError("could not parse server response")

    def _send(self, cmd):
        print "sent: "+cmd
        self._conn.write(cmd + "\n")
        self._handle_server_msgs()

    def _send_recv(self, cmd):
        self._conn.write(cmd + "\n")
        return self._readl()

    def _readl(self):
        return self._conn.read_until("\n").strip()   

    # get >=1 msgs from server
    def _handle_server_msgs(self):

        ignored_msgs = ("ignore", "listen", "key")
        got_success = False

        results = [self._readl()]
        results.extend(self._conn.read_very_eager().split())

        for result in results:
            print "HM: " + result
            if result.split()[0] in ignored_msgs:
                # TODO dispatch
                print "ignored_msg: " + result
                continue
            elif result == "success":
                got_success = True
            elif result == "bye":
                print "server shutdown"
            elif result.split()[0] == "huh?":
                raise ServerError(result)
            else:
                raise ServerError("unknown svr msg %s" % result)

        return got_success

    def add_screens(self, *args):
        for arg in args:
            if not isinstance(arg, Screen):
                raise TypeError
            self.screens.append(arg)
            arg.client = self

    def remove_screens(self, *args):
        for arg in args:
            if not arg in self.screens:
                raise IndexError
            self._send("screen_del %s" % arg.name)
            self.screens.remove(arg)
            arg.client = None

    def update(self):
        for screen in self.screens:
            screen.update()

    def add_key(self, keyname):
        """
        Tell the server you want to handle a keypress.
        keyname should be "Up", "Down", "Enter", "Escape", etc.
        """
        self._send("client_add_key %s" % keyname)

    def del_key(self, keyname):
        """
        Tell the server you no longer want to handle the key.
        """
        self._send("client_del_key %s" % keyname)

class Screen(object):
    def __init__(self):
        self.name = _name_gen(self)
        self.on_server = False
        self.widgets = []
        self.client = None

    def add_widgets(self, *args):
        """
        Implement the widget_add command, return server answer
        """
        for arg in args:
            if not isinstance(arg, Widget):
                raise TypeError
            self.widgets.append(arg)
            arg.screen = self

        #self.client._send("widget_add %s %s %s" %
        #    (self.name, name, type))

    def remove_widgets(self, *args):
        for arg in args:
            if not arg in self.widgets:
                raise IndexError
            self._send("widget_del %s %s" % (self.name, arg.name))
            arg.on_server = False
            self.widgets.remove(arg)

    def set(self, **kwargs):
        """
        Implement the screen_set command, return server answer
        """

        params = dict(
                      name="name",
                      width="wid",
                      height="hgt",
                      priority="priority",
                      duration="duration",
                      timeout="timeout",
                      heartbeat="heartbeat",
                      backlight="backlight",
                      cursor_mode="cursor",
                      cursor_x="cursor_x",
                      cursor_y="cursor_y"
                     )

        print kwargs

        for arg, val in kwargs.iteritems():
            if arg in params:
                self.client._send("screen_set %s -%s %s" %
                     (self.name, params[arg], val))

    def update(self):
        if not self.on_server:
            self.client._send("screen_add %s" % self.name)
            self.on_server = True
        for widget in self.widgets:
            widget.update()

#
# virtual base class, never instantiate
#
class Widget(object):
    def __init__(self):
        self.name = _name_gen(self)
        self.dirty = True
        self.screen = None
        self.on_server = False

    def __setattr__(self, name, value):
        if name != "dirty":
            super(Widget, self).__setattr__("dirty", True)
        super(Widget, self).__setattr__(name, value)

    def update(self, data):
        if not self.on_server:
            self.screen.client._send("widget_add %s %s %s" %
                (self.screen.name, self.name, self.type))
            self.on_server = True
        if not self.dirty:
            return
        self.screen.client._send("widget_set %s %s %s" % (self.screen.name, self.name, data))
        self.dirty = False

class StringWidget(Widget):
    def __init__(self, x=None, y=None, text=None):
        super(StringWidget, self).__init__()
        self.x = x
        self.y = y
        self.text = text
        self.type = "string"

    def update(self):
        super(StringWidget, self).update("%s %s %s" % (self.x, self.y, self.text))

class HBarWidget(Widget):
    def __init__(self, x=None, y=None, length=None):
        super(HBarWidget, self).__init__()
        self.x = x
        self.y = y
        self.length = length
        self.type = "hbar"

    def update(self):
        super(HBarWidget, self).update("%s %s %s" % (self.x, self.y, self.length))

class VBarWidget(Widget):
    def set(self, x, y, length):
        super(VBarWidget, self).set("%s %s %s" % (x, y, length))

class IconWidget(Widget):
    def set(self, x, y, icon):
        super(IconWidget, self).set("%s %s %s" % (x, y, icon))

class TitleWidget(Widget):
    def set(self, title):
        super(TitleWidget, self).set(title)

class ScrollerWidget(Widget):
    """
    Positive speeds indicate frames per movement.
    Negative speeds indicate movements per frame.
    """
    def set(self, left, top, right, bottom, direction, speed, text):
        super(ScrollerWidget, self).set("%s %s %s %s %s %s %s" %
            (left, top, right, bottom, direction, speed, text))

class FrameWidget(Widget):
    """
    Not implemented yet
    """
    pass

class NumWidget(Widget):
    def set(self, x, num):
        super(NumWidget, self).set("%s %s" % (x, num))

