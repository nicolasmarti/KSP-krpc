import krpc
import time
import math

from utils import *

address = "192.168.3.14"

if __name__ == "__main__":

    conn = krpc.connect(name='test', address=address)
    
    ########################################

    # check list
    def is_engaged( autopilot ):
        try:
            v = autopilot.error
            return True
        except:
            return False

    while True:


        space_center = conn.space_center
        vessel = space_center.active_vessel
        ctrl = vessel.control
        flight = vessel.flight()
        autopilot = vessel.auto_pilot
        
        print( "0) stage stats" )
        print( "1) takeoff" )
        print( "2) execute next node" )
        if is_engaged( autopilot ):
            print( "3) disengage autopilot" )
        else:
            print( "3) engage autopilot" )
        print( "4) circularize @ peri" )
        print( "5) circularize @ apo" )
        print( "6) autoscience" )
        print( "7) change apo" )
        print( "8) change peri" )
        print( "9) remove nodes" )
        print( "10) change to previous vessel" )
        print( "11) change vessel name" )
        print( "12) jump to next SOI" )
        print( "13) autostage" )
        
        x = int(input("??? "))

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

        
        # take off
        elif x == 1:
            # taking off
            print( "###### Taking Off ######" )
            target = float(input( "target apo (in km)" ))
            takeoff_iterator = takeoff( conn,
                                        start_angle = 90.0,
                                        start_height = 20000.0,
                                        stop_angle = 30.0,
                                        stop_height = 50000.0,
                                        heading = 90.0,
                                        target_apo = target * 1000.0 + 600000.0 # + diameter of kerbin ... stupid !!!
                                        #target_apo = 2.0 * 100.0 * 1000.0 + 600000.0 # + diameter of kerbin ... stupid !!!
            )

            continuous_science = input( "autoscience?? [y/??]" )
            
            for takeoff_data in takeoff_iterator:

                try:
                    if auto_stage( conn ):
                        vessel.control.throttle = 0.0
                        stats = stage_engine_stats( vessel, ctrl.current_stage )
                        print( ctrl.current_stage, stats )
                        if stats is None:
                            print( "stats is None" )
                            if vessel.control.current_stage > 0:
                                print( "not last stage ==> continue" )
                                continue
                            vessel.control.throttle = 0.0
                            print( vessel.control.current_stage, stats, "returning from execute")
                            break
                        else:
                            vessel.control.throttle = 1.0

                    if continuous_science == "y":
                        autorun_science( conn, debug = False, transmit = True )
                    
                except Exception as e:
                    print( e )
                    pass

                try:
                    #autorun_science( conn, debug = False, transmit = True )
                    pass
                except Exception as e:
                    print( e )
                    pass

            # circularize @ apoapsis + deployment
            if True:
                # circularize @ apo
                print( "###### circularize ######" )
                change_periapsis_node( conn, vessel, vessel.orbit.apoapsis_altitude )

                # deploy all antennas / solar panel
                print( "###### deploy antennas & solar panel ######" )
                deploy_all_antennas( vessel )
                deploy_all_solar_panel( vessel )

                
        # execute node
        elif x == 2:
            node = vessel.control.nodes[0]
            for x in execute_next_node( conn, vessel, node ):
                try:
                    #autorun_science( conn, debug = False, transmit = False )
                    pass
                except Exception as e:
                    print( e )
                    pass

        # return
        elif x == 3:

            if is_engaged( autopilot ):

                vessel.auto_pilot.disengage()

            else:
                
                print( "1) orbital prograde" )
                print( "2) orbital retrograde" )
                print( "3) surface retrograde" )
                print( "4) pitch" )

                x = int(input("??? "))

                if x == 0:
                    break
                elif x == 1:                    
                    vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
                    vessel.auto_pilot.target_direction = ( 0.0, 1.0, 0.0 )
                elif x == 2:                    
                    vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
                    vessel.auto_pilot.target_direction = ( 0.0, -1.0, 0.0 )
                elif x == 3:                    
                    vessel.auto_pilot.reference_frame = vessel.surface_velocity_reference_frame
                    vessel.auto_pilot.target_direction = ( 0.0, -1.0, 0.0 )
                elif x == 4:
                    vessel.auto_pilot.target_pitch = float( input("pitch?? "))
                
                vessel.auto_pilot.engage()


        # circularize @ periapsis
        elif x == 4:
            print( "###### circularize ######" )
            change_apoapsis_node( conn, vessel, vessel.orbit.periapsis_altitude, execute = False )

        # circularize @ apoapsis
        elif x == 5:
            print( "###### circularize ######" )
            change_periapsis_node( conn, vessel, vessel.orbit.apoapsis_altitude, execute = False )

        # autoscience
        elif x == 6:
            try:
                ( autorun_science( conn, debug = True, transmit = True, force_transmit = True ) )
                pass
            except Exception as e:
                print( e )
                pass

            
        # some extra manoeuver
        elif x==7:
            new_apo = eval(input("new apo? "))
            change_apoapsis_node( conn, vessel, new_apo, execute = False )

        elif x==8:
            new_peri = eval(input("new peri? "))
            change_periapsis_node( conn, vessel, new_peri, execute = False )

        elif x == 9:
            node = vessel.control.remove_nodes()

        elif x == 10:
            idx = space_center.vessels.index( space_center.active_vessel )
            space_center.active_vessel = space_center.vessels[idx-1 if idx > 0 else -1]
            
        elif x == 11:
            new_name = input("new name?")
            space_center.active_vessel.name = new_name

        elif x == 12:
            orbit = space_center.active_vessel.orbit
            dt = orbit.time_to_soi_change
            space_center.warp_to( space_center.ut + dt - 2.0, max_rails_rate = 100000000.0,  )

        elif x == 13:
            auto_stage( conn )
            
        elif False:
            print("waiting for deploying the parachute")
            while not auto_parachute( conn ):
                try:
                    autorun_science( conn, debug = False, transmit = False )
                    pass
                except Exception as e:
                    print( e )
                    pass
                time.sleep( 1 )

            print("parachutes deployed")
            print("autopilot disengage")
            vessel.auto_pilot.disengage()

            print("legs extended")
            deploy_all_leg( vessel )










            
