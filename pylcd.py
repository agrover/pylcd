# Copyright (C) 2002 Tobias Klausmann
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

def _name_clean(name):
    """
    All names used as IDs can't have whitespace
    """
    return "".join(name.split())

class Client(object):
    """
    This class opens a connection to the LCD deamon
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
        self._conn.write(cmd+"\n")
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

class Screen(object):
    def __init__(self, client, name):
        self.client = client
        self.name = _name_clean(name)

    def widget_add(self,id,type,params=""):
        """
        Implement the widget_add command, return server answer
        """
        self.client._send("widget_add %s %s %s" % (id,type,params))

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

