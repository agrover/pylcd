#!/usr/bin/python -tt
import sys
import pylcd
import os

c = pylcd.Client()
s = pylcd.Screen()
w1 = pylcd.StringWidget(1, 1, "Hello from Python")
w2 = pylcd.StringWidget(1, 2, "chars are %s x %s" % (c.c_width, c.c_height))
s.add_widgets(w1, w2)
if c.d_height == 4 and c.d_width == 20:
    w3 = pylcd.HBarWidget(1, 4, 20)
    s.add_widgets(w3)
c.add_screens(s)
c.update()

print "Screens added: %d" % len(c.screens)

try:
    raw_input("Press a key to continue")
except EOFError:
    print "\nEOF"

print "Exit."
