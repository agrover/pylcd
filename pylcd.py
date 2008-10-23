# Copyright (C) 2002 Tobias Klausmann
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
__author__="klausman-spam@schwarzvogel.de"
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

class Client(object):
    """
    This class opens a connection to the LCD daemon
    on the specified host and encapsulates all the
    functions of the LCDd protocol.
    """
    def __init__(self, host="localhost", port=13666, name=None):
        """
        Connect to the LCD daemon.
        """
        self._conn = Telnet(host,port)
        self.screens = []

        line = self._send_recv("hello")
        
        try:
            (self.state,
             self.server,
             self.s_version,
             c,
             self.proto,
             self.type,
             c,
             ds_width,
             c,
             ds_height,
             c,
             cs_width,
             c,
             cs_height) = line.split()

            self.d_width = int(ds_width)
            self.d_height = int(ds_height)
            self.c_width = int(cs_width)
            self.c_height = int(cs_height)

        except ValueError:
            self.ds_width="0"
            self.ds_height="0"
            self.cs_width="0"
            self.cs_height="0"
            raise ServerError

        if name:
            self.client_set(name)
        else:
            self.name = None

    def _handle_server_msgs(self):

        ignored_msgs = ("ignore", "listen", "key")

        while True:
            result = self._readl()
            if result.split()[0] in ignored_msgs:
                continue
            elif result == "success":
                return
            elif result == "bye":
                print "server shutdown"
            elif result.split()[0] == "huh?":
                raise ServerError(result)
            else:
                print "unknown svr msg %s" % result
            

    def _send(self, cmd):
        """
        Send "cmd" plus a linefeed to the server.
        """
        print cmd
        self._conn.write(cmd+"\n")

        # ignore listen/ignore for now
        result = self._readl()
        while True:
            if result.startswith("ignore") or result.startswith("listen"):
                result = self._readl()
                continue
            if result != "success":
                raise ServerError(result)
            else:
                return

    def _send_recv(self, cmd):
        self._conn.write(cmd + "\n")
        return self._readl()

    def _readl(self):
        """
        Read and return a whole line. May block.
        """
        line = self._conn.read_until("\n").strip()
        print line
        return line
        #return self._conn.read_until("\n").strip()   
        
    def getinfo(self):
        """
        Print information gathered during connect().
        """
        print "Connection state:",  self.state
        print "Server type:", self.server
        print "Server version: ", self.s_version
        print "Protocol version:",  self.proto
        print "LCD type:", self.type
        print "Display size: %sx%s (%s)"%(self.d_width,self.d_height,self.d_width*self.d_height)
        print "Cell size: %sx%s (%s)"%(self.c_width,self.c_height,self.c_width*self.c_height)

    def set_name(self, name):
        """
        Set the client name. Don't know where this is visible.
        """

        self.name = _name_clean(name)
        self._send("client_set -name %s" % self.name)

    def screen_add(self, name):
        """     
        Implement the screen_add command, return server answer
        """
 
        self._send("screen_add %s" % name)
        new_screen = Screen(self, name)
        self.screens.append(new_screen)
        return new_screen

    def screen_del(self, screen):
        """     
        Implement the screen_del command, return server answer
        """

        if not screen in self.screens:
            raise IndexError

        self._send("screen_del %s"%id)
        self.remove(screen)

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
    def __init__(self, client, name):
        self.client = client
        self.name = _name_clean(name)

    def widget_add(self, name, type):
        """
        Implement the widget_add command, return server answer
        """
        self.client._send("widget_add %s %s %s" %
            (self.name, name, type))

        if type in widget_types:
            return widget_types[type](self, name)

    def widget_del(self, name):
        """
        Implement the widget_del command, return server answer
        """
        self.client._send("widget_del %s %s" %
            (self.screen.name, self.name))

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

class Widget(object):
    def __init__(self, screen, name):
        self.screen = screen
        self.name = _name_clean(name)

    def set(self, data):
        """     
        Implement the widget_set command, return server answer
        """
        self.screen.client._send("widget_set %s %s %s" % (self.screen.name, self.name, data))

class StringWidget(Widget):
    def set(self, x, y, text):
        super(StringWidget, self).set("%s %s %s" % (x, y, text))

class HBarWidget(Widget):
    def set(self, x, y, length):
        super(HBarWidget, self).set("%s %s %s" % (x, y, length))

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

widget_types = {
"string" : StringWidget,
"hbar" : HBarWidget,
"vbar" : VBarWidget,
"icon" : IconWidget,
"title" : TitleWidget,
"scroller" : ScrollerWidget,
"frame" : FrameWidget,
"num" : NumWidget
}
