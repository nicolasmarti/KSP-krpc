import krpc
import time
import math

from utils import *

address = "192.168.3.14"

if __name__ == "__main__":

    conn = krpc.connect(name='test', address=address)
    
    ########################################

    # check list

    while True:

        print( "0) stage stats" )
        print( "1) Fusée de test K-7" )

        x = int(input("???"))

        space_center = conn.space_center
        vessel = space_center.active_vessel
        ctrl = vessel.control
        flight = vessel.flight()
        autopilot = vessel.auto_pilot

        if x == 0:
            print( ctrl.current_stage )
            for stage in range( 0, ctrl.current_stage + 1 ):
                print("#### %d ####" % stage )
                d = parts( vessel, stage )
                if "engine" in d:
                    print( ";".join( [ x.part.name for x in d["engine"] ] ) )
                print( "ressources:", stage_resources_amounts( vessel, stage ) )
                print( "engines: ", stage_engine_stats( vessel, stage ) )
        
        elif x == 1:

            print( "Setting up control" )

            
            # not available
            #ctrl.sas_mode = conn.space_center.SASMode.stability_assist
            #ctrl.sas = True
            #vessel.auto_pilot.target_roll = 0.0            

            #vessel.auto_pilot.target_pitch = 90.0
            #autopilot.engage()
        
            autopilot.disengage()
            
            print( "activate engine" )
            ctrl.activate_next_stage()

            ascending = True
            while ascending:

                alt1 = vessel.flight().surface_altitude
                time.sleep( 2.0 )
                alt2 = vessel.flight().surface_altitude
                falling = alt1 - alt2 > 0.2

                ascending = not falling

            print( "falling: waiting for deploying the chute" )
            while not auto_parachute( conn ):
                pass
        
        else:

            print( "unknown: %s" % str(x) )
