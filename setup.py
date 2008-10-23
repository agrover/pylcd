#! /usr/bin/env python
#
# pylcd
# (c) 2002, 2003 Tobias Klausmann
# You're welcome to redistribute this software under the
# terms of the GNU General Public Licence version 2.0
# or, at your option, any higher version.
#
# You can read the complete GNU GPL in the file COPYING
# which should come along with this software, or visit
# the Free Software Foundation's WEB site http://www.fsf.org
#
# $Id: $

from distutils.core import setup

import pylcd

setup(name = "pylcd", version = pylcd.__version__,
      license = "GNU GPL",
      description = pylcd.__doc__,
      author = "Tobias Klausmann",
      author_email = "klausman-spam@schwarzvogel.de",
      url = "http://www.schwarzvogel.de/software-pylcd.shtml",
      packages= [ "" ],
      scripts = [ "pylcd-test.py" ])
