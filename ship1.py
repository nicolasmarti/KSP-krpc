import krpc
import time
import math

from utils import *

address = "192.168.3.14"

if __name__ == "__main__":

    conn = krpc.connect(name='test', address=address)

    space_center = conn.space_center
    vessel = space_center.active_vessel
    ctrl = vessel.control
    flight = vessel.flight()
    autopilot = vessel.auto_pilot
    
    ########################################
    
    if True:
        print( ctrl.current_stage )
        for stage in range( 0, ctrl.current_stage + 1 ):
            print("#### %d ####" % stage )
            d = parts( vessel, stage )
            if "engine" in d:
                print( ";".join( [ x.part.name for x in d["engine"] ] ) )
            print( "ressources:", stage_resources_amounts( vessel, stage ) )
            print( "engines: ", stage_engine_stats( vessel, stage ) )

        input( "start?" )
            
    if False:
        
        # taking off
        print( "###### Taking Off ######" )
        takeoff_iterator = takeoff( conn,
                                    start_angle = 90.0,
                                    start_height = 10000.0,
                                    stop_angle = 15.0,
                                    stop_height = 50000.0,
                                    heading = 0.0,
                                    target_apo = 100000 + 600000 # + diameter of kerbin ... stupid !!!
        )

        for takeoff_data in takeoff_iterator:

            try:
                if auto_stage( conn ):
                    stats = stage_engine_stats( vessel, ctrl.current_stage )
                    print( ctrl.current_stage, stats )
                    if stats is None:
                        if vessel.control.current_stage > 0:
                            continue
                        vessel.control.throttle = 0.0
                        print( vessel.control.current_stage, stats, "returning from execute")
                        break
            except Exception as e:
                print( e )
                pass

            try:
                autorun_science( conn, debug = False, transmit = True )
                pass
            except Exception as e:
                print( e )
                pass

    if True:

        vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
        vessel.auto_pilot.target_direction = ( 0.0, -1.0, 0.0 )
        vessel.auto_pilot.engage()

        while not auto_parachute( conn ):
            time.sleep( 1 )











            
