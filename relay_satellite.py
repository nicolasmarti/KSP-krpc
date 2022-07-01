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
    r1 = 200000.0
    r2 = 950000.0
    
    ########################################
    
    if True:
        print( ctrl.current_stage )
        for stage in range( 0, ctrl.current_stage + 1 ):
            print("#### %d ####" % stage )
            d = parts( vessel, stage )
            if "engine" in d:
                print( ";".join( [ x.part.tag for x in d["engine"] ] ) )
            print( stage_resources_amounts( vessel, stage ) )
            print( stage_engine_stats( vessel, stage ) )

        input( "start?" )
            
    if False:
        
        # taking off
        print( "###### Taking Off ######" )
        takeoff_iterator = takeoff( conn,
                                    start_angle = 90.0,
                                    start_height = 50000.0,
                                    stop_angle = 15.0,
                                    stop_height = 85000.0,
                                    heading = 90.0,
                                    target_apo = r1 + 600000 # + diameter of kerbin ... stupid !!!
        )

        for takeoff_data in takeoff_iterator:

            try:
                auto_stage( conn )
                pass
            except Exception as e:
                print( e )
                pass


        # circularize @ apo
        print( "###### circularize ######" )
        change_periapsis_node( conn, vessel, vessel.orbit.apoapsis_altitude )

        # deploy all antennas / solar panel
        print( "###### deploy antennas & solar panel ######" )
        deploy_all_antennas( vessel )
        deploy_all_solar_panel( vessel )
    
        
    if False:
        print("###### raising apo ######")
        change_apoapsis_node( conn, vessel, r2 )

    def decouple_and_circularize( tag ):

        part = vessel.parts.with_tag( tag )[0]

        print( part.name )

        part.decoupler.decouple()

        decoupled_vessel = space_center.vessels[-1]

        space_center.active_vessel = decoupled_vessel

        #activate_all_engine( decoupled_vessel )
        decoupled_vessel.control.activate_next_stage()

        change_periapsis_node( conn, decoupled_vessel, r2 )

        space_center.active_vessel = vessel
        
    if True:

        # tag = "decoupler2"
        # parts = vessel.parts.all
        # for part in parts:
        #     if part.tag == tag:
        #         print( part.name, part.tag )
        #         part.decoupler.decouple()

        vessel.control.activate_next_stage()                
        activate_all_engine( vessel )
        change_periapsis_node( conn, vessel, r2, autostage = False )
