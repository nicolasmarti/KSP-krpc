import krpc
import time
import math

#####

def new_parts( vessel ):
    
    res = dict()

    parts = vessel.parts.all

    for part in parts:

        decouple_stage = part.decouple_stage
        activation_stage = part.stage

        print( part.name, ", tag:", part.tag, ", activation stage:", activation_stage, ", decouple stage:", decouple_stage + 1 )
    

def parts( vessel, stage ):

    categories = [
        "engine",
        "antenna",
        "solar_panel"
    ]

    res = dict()

    parts = vessel.parts

    #for part in parts.all:
    for part in parts.in_decouple_stage( stage - 1 ):
        
        pstage = part.decouple_stage

        if pstage != stage - 1:
            continue
        
        if not stage in res:
            res[ stage ] = list()
            for category in categories:
                res[ category ] = list()

        #res[ stage ].append( (part, part.name, part.decouple_stage) )
         
        for category in categories:
            p = part.__getattribute__( category )
            if p is not None:
                res[ category ].append( p )
        
    return res


def stage_resources_amounts( vessel, stage ):
    
    res = dict()

    resources = vessel.resources_in_decouple_stage( stage - 1, False )
    for name in resources.names:
        if not name in res.keys():
            res[ name ] = 0.0
        res[ name ] += resources.amount( name )

    return res

def resources_amounts( vessel ):

    res = dict()
    ctrl = vessel.control

    for stage in range( 0, ctrl.current_stage + 1 ):
        r = stage_resources_amounts( vessel, stage )
        for k in r.keys():
            if not k in res.keys():
                res[k] = r[k]
            else:
                res[k] += r[k]

    return res

def stage_resources_densities( vessel, stage ):
    
    res = dict()

    resources = vessel.resources_in_decouple_stage( stage - 1, False )
    for resource in resources.all:
        name = resource.name
        res[ name ] = resource.density

    return res


def deploy_all_antennas( vessel, revert = False ):

    for part in vessel.parts.all:
        antenna = part.antenna        
        if antenna is not None:
            try:
                antenna.deployed = not revert
                print( part.name, not revert )
            except:
                pass

    return

def deploy_all_solar_panel( vessel, revert = False ):

    for part in vessel.parts.all:
        solar_panel = part.solar_panel        
        if solar_panel is not None:
            try:
                solar_panel.deployed = not revert
                print( part.name, not revert )
            except:
                pass
                    
    return


def deploy_all_parachute( vessel ):

    for part in vessel.parts.all:
        parachute = part.parachute
        if parachute is not None:
            try:
                parachute.arm()
                parachute.deploy()
                print( "deploy", part.name )
            except:
                pass
                    
    return

# not working ...
def deploy_all_leg( vessel, revert = False ):

    for part in vessel.parts.all:
        leg = part.leg
        if leg is not None:
            try:
                leg.deployed = not revert
                print( part.name, not revert, leg.deployed, leg.state, leg.deployable )                
            except:
                pass
                    
    return

def activate_all_engine( vessel, revert = False ):

    for part in vessel.parts.all:
        engine = part.engine
        if engine is not None:
            try:
                engine.active = not revert
                print( part.name, not revert )
            except:
                pass

    return

def stage_mass( vessel, stage ):

    mass = 0.0
    
    parts = vessel.parts

    #print( "----- mass(%d) -----" % stage )
    for part in parts.in_decouple_stage( stage - 1 ):
        #print( part.name, part.mass )
        mass += part.mass
    #print( "----- %f -----" % mass )
        
    return mass

def compute_d_v( isp, m, d_m ):

    return isp * math.log( m / ( m - d_m ) )

def compute_d_m( isp, d_v, m ):

    return m * ( 1.0 - 1.0 / math.exp( d_v / isp) )

def compute_d_t( isp, d_v, m, density, flow_rate, alpha = 1.0 ):

    return compute_d_m( isp, d_v, m )/ ( flow_rate * density * alpha )

def compute_alpha( isp, d_v, m, density, d_t, flow_rate ):

    return compute_d_m( isp, d_v, m )/ ( flow_rate * density * d_t )

def stage_engine_stats( vessel, stage ):

    res = dict()
    
    d = parts( vessel, stage )
    #print( d )
    
    if not ( "engine" in d.keys() and len( d["engine"] ) == 1 ):
        return None

    engine = d["engine"][0]
    part = engine.part

    amounts = stage_resources_amounts( vessel, stage )

    densities = stage_resources_densities( vessel, stage )

    consum = engine.propellant_ratios
    
    isp = engine.vacuum_specific_impulse * 9.82
    thrust = engine.available_thrust
    flow_rate = thrust / isp

    full_consum_l = sum( [ consum[k] for k in consum.keys() ] )
    
    density = sum( [ consum[k] * densities[k] for k in consum.keys() ] ) / sum( [ consum[k] for k in consum.keys() ] )

    d_m_max = sum( [ amounts[k] * densities[k] for k in amounts.keys() ] )
    
    for k in [
            "isp", "density", "d_m_max", "flow_rate"
    ]:
        res[k] = locals()[k]


    return res
    
def monoengine_stage_propulsion_stats( vessel, stage ):

    res =dict()
    
    d = parts( vessel, stage )

    if not ( "engine" in d.keys() and len( d["engine"] ) == 1 ):
        return None

    engine = d["engine"][0]
    part = engine.part

    amounts = stage_resources_amounts( vessel, stage )

    densities = stage_resources_densities( vessel, stage )

    min_time = None

    consum = engine.propellant_ratios

    mass = 0.0

    isp = engine.kerbin_sea_level_specific_impulse * 9.82
    isp_2 = engine.vacuum_specific_impulse * 9.82
    thrust = engine.available_thrust
    flow_rate = thrust / isp
    flow_rate_2 = thrust / isp_2

    full_consum_kg = sum( [ consum[k] * densities[k] for k in consum.keys() ] )
    full_consum_l = sum( [ consum[k] for k in consum.keys() ] )

    ratios_l = dict()
    ratios_kg = dict()

    flow_rates = dict()
    flow_rates_2 = dict()
    full_masses = dict()

    burn_times = dict()
    burn_times_2 = dict()
    
    for k in consum.keys():

        ratios_l[ k ] = consum[k] / full_consum_l
        ratios_kg[ k ] = densities[k] * consum[k] / full_consum_kg

        flow_rates[k] = flow_rate * ratios_kg[ k ]
        flow_rates_2[k] = flow_rate_2 * ratios_kg[ k ]
        
        full_masses[k] = amounts[k] * densities[k]

        burn_times[k] = full_masses[k] / flow_rates[k]
        burn_times_2[k] = full_masses[k] / flow_rates_2[k]

    full_fuel_mass = sum( [ amounts[ k ] * densities[ k ] for k in amounts.keys() ] )
    full_mass = sum( [ stage_mass( vessel, x ) for x in range(0, stage + 1) ] )

    d_v = isp * math.log( full_mass / ( full_mass - full_fuel_mass  ) )
    d_v_2 = isp_2 * math.log( full_mass / ( full_mass - full_fuel_mass  ) )

    res["full_fuel_mass"] = full_fuel_mass
    res["full_mass"] = full_mass

    res["sea_level"] = dict()
    res["sea_level"]["isp"] = isp
    res["sea_level"]["flow_rate"] = flow_rate
    res["sea_level"]["d_v"] = d_v
    res["sea_level"]["burn_time"] = min( [ burn_times[k] for k in consum.keys() ] )
    

    res["vaccum"] = dict()
    res["vaccum"]["d_v"] = d_v_2
    res["vaccum"]["isp"] = isp_2
    res["vaccum"]["flow_rate"] = flow_rate_2
    res["vaccum"]["burn_time"] = min( [ burn_times_2[k] for k in consum.keys() ] )
            
    res["current"] = dict()
    res["current"]["isp"] = engine.specific_impulse * 9.82
    if res["current"]["isp"] == 0.0:
        res["current"]["isp"] = isp_2
    
    res["current"]["flow_rate"] = thrust / res["current"]["isp"]
    res["current"]["d_v"] = res["current"]["isp"] * math.log( full_mass / ( full_mass - full_fuel_mass  ) )
    
    
    return res

def monoengine_stage_burn_time( vessel, stage, target_d_v, category = "current" ):

    stats = monoengine_stage_propulsion_stats( vessel, stage )

    if stats is None: return( target_d_v, 0.0 )
    
    d = stats[category]
    
    d_v = d["d_v"]
    
    if d_v > target_d_v:
        # fuel mass to burn
        fuel_mass = stats["full_mass"] * ( 1.0 - 1.0 / (math.exp( ( target_d_v / d["isp"] ) )) )
        return ( 0.0, fuel_mass / d["flow_rate"] )
    else:
        return ( target_d_v - d_v, stats["full_fuel_mass"] / d["flow_rate"] )

# for current stage    
def throttle_for_delta_V_burn_time( vessel, delta_v, d_t ):

    try:
        stats = monoengine_stage_propulsion_stats( vessel, vessel.control.current_stage )
    except:
        return 0.0

    d = stats["current"]
    
    d_m = stats["full_mass"] * ( 1.0 - 1.0 / (math.exp( ( delta_v / d["isp"] ) )) )

    return min( [ (d_m / 1.0), (d_m / d_t) ] ) / d["flow_rate"]

def throttle_for_delta_V_burn_time_quick( vessel, delta_v, d_t, flow_rate, isp ):

    # try:
    #     stats = monoengine_stage_propulsion_stats( vessel, vessel.control.current_stage )
    # except:
    #     return 0.0
    
    d_m = vessel.mass * ( 1.0 - 1.0 / (math.exp( ( delta_v / isp ) )) )

    return min( [ (d_m / 1.0), (d_m / d_t) ] ) / flow_rate


###
def multistage_burn_time( vessel, target_d_v, category = "current" ):
    control = vessel.control
    d_v = target_d_v
    burn_time = 0.0
    stage = control.current_stage
    while stage >= 0 and d_v >= 0.0:
        ( d_v, bt ) = monoengine_stage_burn_time( vessel, stage, d_v, category = category )
        burn_time += bt
        #print ( stage, d_v, burn_time )
        stage -= 1
        
    return ( d_v, burn_time )

def visavis(
        mu, # GM
        r, # distance between the body
        a # semi-major axis
):
    return math.sqrt(mu*((2./r)-(1./a1)))

def change_orbit_dv( vessel, target, r ):
    
    ctrl = vessel.control
    flight = vessel.flight()
    
    mu = vessel.orbit.body.gravitational_parameter
    a1 = vessel.orbit.semi_major_axis
    a2 = target

    #print( "r, target, a1, a2", r, target, a1, a2 )
    
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1

    return delta_v


def execute_next_node( conn, vessel, node, autostage = True ):

    print( "execute node" )
    ctrl = vessel.control

    print( node.delta_v )
    
    delta_v = node.delta_v

    ( remaining_delta_v, burn_time ) = multistage_burn_time( vessel, delta_v )

    burn_time = max( 2.0, burn_time )
    
    print( "burn_time:", burn_time )

    try:
        ctrl.sas = False
    except:
        pass

    prev_remaining_delta = node.remaining_delta_v
    stats = stage_engine_stats( vessel, ctrl.current_stage )
    print( ctrl.current_stage, stats )
        
    min_burn_time = 0.1
    alpha_threshold = 0.01
    delta_v_threshold = 0.075

    last_time = None

    d_v = delta_v
    
    vessel.auto_pilot.reference_frame = node.reference_frame
    vessel.auto_pilot.target_direction = node.burn_vector( node.reference_frame )
    vessel.auto_pilot.engage()
    ctrl.rcs = True

    print( "pointing ..." )
    while abs(vessel.auto_pilot.error) > 10.0:
        time.sleep( .1 )
    print( "pointed to", vessel.auto_pilot.error )
    
    leading_time = 40.0
    warp_time = (burn_time / 2.0) + leading_time

    min_warp_time = node.ut - conn.space_center.ut

    warp_time = max( 0.0, min( warp_time, min_warp_time ) )
    print( "warping for ...", warp_time )
    if warp_time > 10.0:

        try:
            ctrl.sas_mode = conn.space_center.SASMode.stability_assist
            ctrl.sas = True
            ctrl.rcs = True
            time.sleep( 1 )
        except:
            pass                    
            ctrl.sas = False
            ctrl.rcs = False
            
        vessel.auto_pilot.disengage()

        conn.space_center.warp_to( node.ut - warp_time, max_rails_rate = 100000000.0, max_physics_rate = 3.0 )

        print( "" )
        
        vessel.auto_pilot.reference_frame = node.reference_frame
        vessel.auto_pilot.target_direction = node.burn_vector( node.reference_frame )
        vessel.auto_pilot.engage()
        ctrl.rcs = True

        print( "unwarping, taking time ..." )
        while node.time_to - (burn_time / 2.0) > 0.0:
            pass

    ctrl.rcs = True        
    vessel.auto_pilot.reference_frame = node.reference_frame
    vessel.auto_pilot.target_direction = node.burn_vector( node.reference_frame )
    vessel.auto_pilot.engage()
        
    start_time = time.time()

    m = vessel.mass

    prev_delt_v = node.remaining_delta_v
    
    while (
            d_v > 0.0            
    ):

        if autostage:
            if auto_stage( conn ):
                #time.sleep( 0.5 )
                stats = stage_engine_stats( vessel, ctrl.current_stage )
                print( ctrl.current_stage, stats )
                if stats is None:
                    if vessel.control.current_stage > 0:
                        continue
                    vessel.control.throttle = 0.0
                    print( vessel.control.current_stage, stats, "returning from execute_next_node")
                    return
        
        m = vessel.mass

        d_v = node.remaining_delta_v
        
        predicated_burn_time = compute_d_t( stats["isp"], d_v, vessel.mass, stats["density"], stats["flow_rate"] )

        clamped_predicated_burn_time = max( min_burn_time, predicated_burn_time )

        vessel.control.throttle = max( 0.0, min( 1.0, ( compute_alpha( stats["isp"],  d_v, m, stats["density"], clamped_predicated_burn_time, stats["flow_rate"] ) ) ) )

        if ( (vessel.control.throttle < alpha_threshold and
             node.remaining_delta_v < delta_v_threshold) or
             node.remaining_delta_v > prev_delt_v + 0.005
        ):
            print( "reached minimal throttle threshold" )
            print( "%f < %f: %r" % (vessel.control.throttle, alpha_threshold, vessel.control.throttle < alpha_threshold) )
            print( "%f < %f: %r" % ( node.remaining_delta_v, delta_v_threshold, node.remaining_delta_v < delta_v_threshold ) )
            print( "%f > %f: %r" % ( node.remaining_delta_v, prev_delt_v, node.remaining_delta_v > prev_delt_v ) )                   
            vessel.control.throttle = 0.0
            break

        prev_delt_v = node.remaining_delta_v
        
        yield( None )
            
    print( "execution_time:", time.time() - start_time )

    ctrl.rcs = False
    vessel.control.throttle = 0.0
    vessel.auto_pilot.disengage()

    try:
        ctrl.sas_mode = conn.space_center.SASMode.stability_assist
        ctrl.sas = True
        time.sleep( 3 )
        ctrl.sas = False
    except:
        pass
    
    node.remove()

def change_apoapsis_node( conn, vessel, target_apo, autostage = True, execute = True ):

    print( "setting node" )
    delta_v = change_orbit_dv( vessel, (target_apo + vessel.orbit.body.equatorial_radius + vessel.orbit.periapsis) / 2.0, vessel.orbit.periapsis )
    node = vessel.control.add_node(
        conn.space_center.ut + vessel.orbit.time_to_periapsis, prograde=delta_v
    )

    if execute:
        print( "execute node" )
        for x in execute_next_node( conn, vessel, node, autostage = autostage ):
            pass

def change_periapsis_node( conn, vessel, target_peri, autostage = True, execute = True ):

    print( "setting node" )
    delta_v = change_orbit_dv( vessel, (target_peri + vessel.orbit.body.equatorial_radius + vessel.orbit.apoapsis) / 2.0, vessel.orbit.apoapsis )
    node = vessel.control.add_node(
        conn.space_center.ut + vessel.orbit.time_to_apoapsis, prograde=delta_v
    )

    if execute:
        print( "execute node" )
        for x in execute_next_node( conn, vessel, node, autostage = autostage ):
            pass


# auto run parachute
def auto_parachute( conn ):
    delay = 0.1
    try:
        space_center = conn.space_center
        active_vessel = space_center.active_vessel
        parts = active_vessel.parts
        parachutes = parts.parachutes        
        
        ###
            
        alt1 = active_vessel.flight().surface_altitude
        time.sleep( delay )
        alt2 = active_vessel.flight().surface_altitude
        falling = alt1 - alt2 > 0.2

        # should I deploy ?
        if ( alt1 < 5000.0 + active_vessel.flight().elevation and
             falling
        ):
            try:
                print( "deploy" )
                deploy_all_parachute(active_vessel)
                return True
            except Exception as e:
                print("deploy by hand:")
                import traceback
                print( traceback.format_exc() )
                return True
                pass
        
                
    except Exception as e:
        import traceback
        # print( "" )
        # print( traceback.format_exc() )
        # time.sleep( 0.50 )
        raise e

    return False

# auto run science
def autorun_science( conn, debug = False, transmit = True, force_transmit = False ):

    already_done_science = list()
    
    try:
        
        space_center = conn.space_center
        vessel = space_center.active_vessel
        parts = vessel.parts
        experiments = parts.experiments

        ### can we transmit the data
        can_transmit = False
        antennas = parts.antennas
        for antenna in antennas:
            part = antenna.part
            can_transmit |= antenna.can_transmit
            
        ### we group the experiments by types
        experiment_types = dict()
        for experiment in experiments:
            name = experiment.part.name
            if not name in experiment_types.keys():
                experiment_types[name] = list()
            experiment_types[name].append( experiment )

            
        exp_acted = False
            
        ### let's roll around the experminent
        for ty in experiment_types.keys():

            #print("----------- %s ----------" % ty )
            
            exps = experiment_types[ty]
        
            for experiment in exps:

                try:
                    
                    exp_acted = False

                    part = experiment.part

                    #print( "#### %s ####" % part.name )

                    for field in [
                            # "available",
                            # "has_data",
                            # "deployed",
                            # "rerunnable"
                    ]:
                        print( field, experiment.__getattribute__( field ) )
                        pass

                    def science_value():
                        return sum([
                            data.transmit_value
                            for data in experiment.data
                        ])

                    # should I run ?
                    if ( experiment.available and # we can run the experiment
                         not experiment.has_data and # the experiement has not been run yet
                         not experiment.science_subject.title in already_done_science and # it is not done yet
                         not experiment.science_subject.is_complete and # not completed
                         experiment.science_subject.science < experiment.science_subject.science_cap # there is still some science to get
                    ):
                        try:
                            already_done_science.append( experiment.science_subject.title )
                            experiment.run()
                            if debug or science_value() > 0.0:
                                print( part.name, "run", experiment.science_subject.title, science_value() )
                            exp_acted = True
                        except:
                            pass

                    resources = resources_amounts( vessel )

                    # should I transmit ?
                    if ( (experiment.rerunnable or force_transmit) and
                         experiment.has_data and
                         can_transmit and
                         transmit and
                         'ElectricCharge' in resources.keys() and
                         resources['ElectricCharge'] > 50.0
                    ):
                        if science_value() > 0.0:
                            if True:
                                print( part.name, "transmit", science_value() )
                            experiment.transmit()
                            experiment.reset()
                            exp_acted = True


                    # should I reset ?
                    elif ( experiment.has_data and
                         science_value() == 0.0
                    ):
                        if debug:
                            print( part.name, "reset" )
                        experiment.reset()

                    if exp_acted: break
                except:
                    pass
    except:
        import traceback
        print( traceback.format_exc() )
        # time.sleep( 0.50 )
        return exp_acted

def auto_stage( conn ):
        
    try:
        space_center = conn.space_center
        vessel = space_center.active_vessel
        ctrl = space_center.active_vessel.control

        current_stage = ctrl.current_stage

        res = stage_resources_amounts( vessel, current_stage )
        
        amount = 0.0
        for name in res.keys():
            if name in ["SolidFuel", "LiquidFuel", "Oxidizer"]:
                amount += res[ name ]
                
        if amount < 0.1 and current_stage > 0:
            prev_stage = current_stage
            old_throttle = vessel.control.throttle
            vessel.control.throttle = 0.0
            ctrl.activate_next_stage()
            current_stage = ctrl.current_stage
            print( "####  ####" )
            print( "activate new stage: %d -> %d" % (prev_stage, current_stage) )
            for k in res:
                print( k, res[k] )
            vessel.control.throttle = old_throttle
            return True

    except Exception as e:
        import traceback
        # print( "" )
        print( traceback.format_exc() )
        # time.sleep( 0.50 )
        # raise e
        
    return False
        

def linear_interpolation(
        XYs,
        x
):

    Xs, Ys = zip( *XYs )
    
    if x <= Xs[0]:
        return Ys[0]

    if Xs[-1] <= x:
        return Ys[-1]

    for i in range( 0, len( Xs ) - 1 ):

        if Xs[i] <= x <= Xs[i+1]:

            slope = (Ys[i+1] - Ys[i]) / (Xs[i+1] - Xs[i])
            
            return Ys[i] + slope * ( x - Xs[i] )

    raise Exception("linear_interpolation: no bracket found !")
    
    
def takeoff( conn,
             start_angle = 90.0,
             start_height = 200.0,
             stop_angle = 60.0,
             stop_height = 2000.0,
             heading = 90.0,
             target_apo = 80000.0
):
        
    try:
        space_center = conn.space_center
        vessel = space_center.active_vessel
        ctrl = vessel.control
        flight = vessel.flight()
        autopilot = vessel.auto_pilot
        orbit = vessel.orbit
        
        vessel.auto_pilot.target_pitch = start_angle
        if heading is not None:
            vessel.auto_pilot.target_heading = heading
        vessel.auto_pilot.target_roll = 0.0

        try:
            ctrl.sas_mode = space_center.SASMode.stability_assist
            ctrl.sas = True
        except:
            pass
        
        autopilot.engage()

        ctrl.throttle = 1.0 # might want to have something a bit more clever

        current_stage = ctrl.current_stage

        res = stage_resources_amounts( vessel, current_stage )

        amount = 0.0
        for name in res.keys():
            if name in ["SolidFuel", "LiquidFuel", "Oxidizer"]:
                amount += res[ name ]

        if amount < 0.01:
            ctrl.activate_next_stage() 

        #print( orbit.apoapsis, target_apo ) 
        while orbit.apoapsis <= target_apo: # adding a condition if target connot be reach ?

            angle = linear_interpolation( [ (start_height, start_angle), (stop_height, stop_angle) ], flight.surface_altitude )
            
            autopilot.target_pitch = angle

            if orbit.apoapsis > 20000.0 + 600000.0:
                ctrl.rcs = True
            
            # while flight.terminal_velocity > flight.speed:
            #     ctrl.throttle -= 0.02
                
            # while flight.terminal_velocity < flight.speed:
            #     ctrl.throttle += 0.02
            
            yield( angle, autopilot.pitch_error, autopilot.heading_error, autopilot.roll_error )
            
        ctrl.throttle = 0.0
        try:
            ctrl.sas = False
        except:
            pass
            
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        pass
    
    return 
