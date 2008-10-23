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

class Client(object):
    """
    This class opens a connection to the LCD deamon
    on the specified host and encapsulates all the
    functions of the LCDd protocol.
    """
    def __init__(self, host="localhost", port=13666):
        """
        Connect to the LCD daemon. Do *not* send
        "hello" (connect() is used for that).
        """
        self._conn = Telnet(host,port)
        self.screens = []
        self.state = "unconnected"
        self.server = None
        self.s_version = None
        self.proto = None
        self.type = None
        self.d_width = None
        self.d_height = None
        self.c_width = None
        self.c_height = None
        #self.connect()

    def send(self,cmd):
        """
        Send "cmd" plus a linefeed to the server.
        """
        self._conn.write(cmd+"\n")

    def read(self):
        """
        Read very eagerly, but not necessarily a whole line.
        Return read data.
        """
        return self._conn.read_very_eager()

    def readl(self):
        """
        Read and return a whole line. May block.
        """
        return self._conn.read_until("\n")    
        
    def connect(self):
        """
        Send connect message ("hello") to server and
        return connection message. Also set internal
        variables that can be read via getinfo().
        """
        self.send("hello")
        line = self.readl().strip()
        
        try:
            (self.state,
             self.server,
             self.s_version,
             c,
             self.proto,
             self.type,
             c,
             self.ds_width,
             c,
             self.ds_height,
             c,
             self.cs_width,
             c,
             self.cs_height) = line.split()

        except ValueError:
            self.ds_width="0"
            self.ds_height="0"
            self.cs_width="0"
            self.cs_height="0"

        self.d_width = int(self.ds_width)
        self.d_height = int(self.ds_height)
        self.c_width = int(self.cs_width)
        self.c_height = int(self.cs_height)

        line = line + self.read()

        return line

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

    def client_set(self,id):
        """
        Implement the client_set command, return server answer
        """
        self.send("client_set %s"%id)
        return self.readl()

    def screen_add(self, name):
        """     
        Implement the screen_add command, return server answer
        """     
        
        self.send("screen_add %s" % name)
        result = self.readl()

        if result == "success":
            new_screen = Screen(self, name)
            self.screens.append(new_screen)
            return new_screen
        else:
            raise ServerError(result)

    def screen_del(self, screen):
        """     
        Implement the screen_del command, return server answer
        """

        if not screen in self.screens:
            raise IndexError

        self.send("screen_del %s"%id)
        result = self.readl()

        if result != "success":
            raise ServerError(result)
        self.remove(screen)


class Screen(object):
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def widget_add(self,id,type,params=""):
        """     
        Implement the widget_add command, return server answer
        """
        self.send("widget_add %s %s %s"%(id,type,params))
        return self.readl()

    def set(self,id,params):
        """     
        Implement the screen_set command, return server answer
        """     
        self.send("screen_set %s %s"%(id,params))
        return self.readl()

class Widget(object):
    def __init__(self, screen, name):
        self.screen = screen
        self.name = name

    def set(self,id,data):
        """     
        Implement the widget_set command, return server answer
        """
        self.send("widget_set %s %s %s" % (self.screen.name, self.name, data))
        return self.readl()

