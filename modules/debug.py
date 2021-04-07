# -*- coding: utf-8 -*-
import sys
import pprint
import config

def errx(msg=None):
    if msg is not None:
        print
        print("[ERROR]: %s" % msg)
    sys.exit('')

def trace(data, **kwargs):
    debug = kwargs.get('debug', config.debug)
    if debug >= 2 or debug == True:
        pp = pprint.PrettyPrinter(indent=1)
        pp.pprint(data)

def debug(level=1, **kwargs):
    out = ''
    if config.debug >= level:
        for key in kwargs:
            value = kwargs[key]
            if len(out) > 0:
                out += " "
            out += key + "=" + "'" + str(value) + "'"
        print("[DEBUG] " + out)
