import krpc
import time
import math
import importlib

##

import prelude
importlib.reload( prelude )

import equations
importlib.reload( equations )

import utils
importlib.reload( utils )

##

print( "repl( %s )>>" % prelude.version() )

##

if False:

    address = "192.168.3.14"

    if not "conn" in globals().keys():

        conn = krpc.connect(name='doudou', address=address)

        print( conn )


    print("done")    

    if False:
        del conn
