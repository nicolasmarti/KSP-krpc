import krpc
import time
import math

#####

from enum import Enum

class Env(Enum):
    VACUUM = 1
    ATMO = 2
    CURRENT = 3

#####

def import_ml( name ):
    import ocaml
    try:
        import os
        folder = os.path.join(
            os.normpath(__file__).split( os.sep )[-1]
        )
    except:
        folder = os.getcwd()

    f = open(
        os.path.join( folder, name + ".ml" ),
        "r"
    )
    content = f.read()
    f.close()

    m = ocaml.compile( content )

    return m

##################

# for fun => to verify in why3

def closure(
        root, # : node
        next_nodes, # : node -> [node]
        filter # : node -> bool
): # set( node )
    
    visited = set() # all the visited nodes: guaranty that the closure will terminate

    result = set() # the subset of visited nodes that have passed the filter
    
    to_visit = set() # next nodes to visit

    to_visit.add( root )
    
    # while there are nodes to visit
    while len(to_visit) > 0:

        # pop the next one to visit
        next_to_visit = to_visit.pop()
         
        # has this node been visited ?
        if next_to_visit in visited:
            # yes: skip and go to the next node
            continue

        # nop: we add it to visited and proceed
        visited.add( next_to_visit )

        # does it pass the filter ?
        if filter( next_to_visit ):

            # this is a valide node to go through and we need to add it
            result.add( next_to_visit )

            # we get the next nodes
            nexts = next_nodes( next_to_visit )

            # we remove those already visited [ this is redundant, but harmless ]
            nexts = set([ next for next in nexts if not next in visited ])
            
            to_visit |= nexts

        else:

            # not a valid nod, we skip, but remember we did visit it
            visited.add( next_to_visit )

        
    return result

##################

g0 = 9.81 # : m s^-2

def compute_d_v(
        isp, # : m s^-1
        m, # : kg
        d_m # : kg
): # : m s^-1

    return isp * math.log( m / ( m - d_m ) )

def compute_d_m(
        isp, # : m s^-1
        d_v, # : m s^-1
        m # kg
): # : kg

    return m * ( 1.0 - 1.0 / math.exp( d_v / isp) )

def compute_d_t(
        isp, # : m s^-1
        d_v, # : m s^-1
        m, # : kg
        density, # : kg m^-3
        flow_rate, # : m^3 s^-1
        alpha = 1.0 # : scalar
): # : s
    
    return compute_d_m( isp, d_v, m ) / ( flow_rate * density * alpha )

def compute_alpha(
        isp, # : m s^-1
        d_v, # : m s^-1
        m, # : kg
        density, # : kg m^-3
        d_t, # : s
        flow_rate # : m^3 s^-1
): # scalar

    return compute_d_m( isp, d_v, m )/ ( flow_rate * density * d_t )

def compute_burning_time(
        flow_rate, # kg s^-1
        ratio, # :scalar = normalized ratio for the resource
        mass # :kg = mass available of the resource
): #: s = the time needed to burn all the resource
    return mass / ( flow_rate * ratio )


##################

class Vessel( object ):

    def __init__( self, conn ):

        self.conn = conn
        self.vessel = conn.space_center.active_vessel

    ######
    
    def active_engine_in_stage( self, stage ):

        parts = self.vessel.parts

        engines = parts.engines

        engines_in_stage_and_active = [
            engine
            for engine in engines
            if engine.part.decouple_stage < stage and engine.part.stage == stage
        ]

        return engines_in_stage_and_active

    def engine_resources( self, engine ):

        part = engine.part

        def next( part ):

            s = set(part.children)
            s.add( part.parent )
            
            return s

        filter = lambda x: x.crossfeed
        
        cross_fueled_next_parts = closure(
            part, # : node
            next, # : node -> [node]
            filter # : node -> bool
        )

        propellant_names = engine.propellant_names

        result = dict( [ (
            name,
            [ 0.0, float("nan"), 0.0 ] # amount [m^3], density, mass [kg]
        ) for name in propellant_names ] )

        for part in cross_fueled_next_parts:

            resources = part.resources
            
            for propellant_name in propellant_names:

                if resources.has_resource( propellant_name ):

                    result[ propellant_name ][ 0 ] += resources.amount( propellant_name )
                    result[ propellant_name ][ 1 ] = resources.density( propellant_name )
                    result[ propellant_name ][ 2 ] += resources.amount( propellant_name ) * resources.density( propellant_name )
        
        
        return result
    
    def engine_stats( self, engine, env = Env.CURRENT ):

        # first we need isp & thrust
        if env == Env.CURRENT:
            thrust = engine.available_thrust
            isp = engine.specific_impulse
        elif env == Env.ATMO:
            thrust = engine.max_thrust
            isp = engine.vacuum_specific_impulse
        elif env == Env.VACUM:
            thrust = engine.max_thrust
            isp = engine.kerbin_sea_level_specific_impulse
        else:
            thrust = float( "nan" )
            isp = float( "nan" )

        # thus we can compute the flow_rate
        flow_rate = thrust / ( isp * g0 )

        # the resources, the ratio for prop flow (renormalize)
        resources = self.engine_resources( engine )        
        ratios = engine.propellant_ratios
        sum_ratios = sum ([ ratios[k] for k in ratios.keys() ])
        
        # then we can compute the maximum time we can thrust 100%
        # given the resources available

        # let's use a helper
            
        burning_time = None

        # for each resource
        for resource in resources:

            # compute its burning time
            ratio = ratios[resources] / sum_ratios
            mass = resources[resource][2]
            resource_burning_time = compute_burning_time(
                flow_rate,
                ratio,
                mass
            )

            # and take the min
            if burning_time is None or resource_burning_time < burning_time:
                burning_time = resource_burning_time
            
        # now from the burning_time, we can compute the mass
        sum_mass_prop = 0.0

        for resource in resources:
            ratio = ratios[resources] / sum_ratios
            sum_mass_prop += flow_rate * ratio * burning_time

        # we need to compute the mass at this point
        stage = engine.part.stage # ????

        # let's grab the parts that should be present
        parts = self.vessel.parts

        parts_present_at_stage = [
            part
            for part in parts.all
            if part.decouple_stage < stage
        ]
        
        # and we compute the full mass
        mass = sum( [ part.mass for part in parts_present_at_stage ] )

        delta_v = compute_d_v( isp * g0, mass, sum_mass_prop )

        stats = dict()
        stats["env"] = env
        stats["d_v"] = delta_v
        stats["d_m"] = sum_mass_prop
        stats["d_t"] = burning_time
        stats["flow_rate"] = flow_rate
        
        return stats

    def stage_delta_v( self, stage, env = Env.CURRENT ):

        # grab each engine
        engines = self.active_engine_in_stage( stage )

        # and sumup the delta_v
        delta_v = sum( [
            self.engine_delta_v( engine, env = env )["d_v"]
            for engine in engines
        ] )
        
        
        return stage_delta_v
    
    ######

    def current_stage( self ):

        return self.vessel.control.current_stage

    ###### 
    
######

if __name__ == "__main__":

    address = "192.168.3.2"
    conn = krpc.connect(name='Landing Site', address=address)

    v = Vessel( conn )

    print( v.current_stage() )
    for stage in range( 0, v.current_stage() + 1 ):
        d_v_vacuum = v.stage_delta_v( stage, Env.VACUUM )
        d_v_atmo = v.stage_delta_v( stage, Env.ATMO )
        print( " ### %d ###: %f <-> %f" % (stage, d_v_atmo, d_v_vacuum) )
        engines = v.active_engine_in_stage( stage )
        for engine in engines:
            max_thrust = engine.max_thrust
            isp_atmo = engine.kerbin_sea_level_specific_impulse
            flow_rate_atmo = max_thrust / ( isp_atmo * g0 )
            isp_vacuum = engine.vacuum_specific_impulse
            flow_rate_vacuum = max_thrust / ( isp_vacuum * g0 )

            ratios = engine.propellant_ratios
            sum_ratios = sum ([ ratios[k] for k in ratios.keys() ])
            for k in ratios.keys(): ratios[k] /= sum_ratios
            
            print(
                engine.part.name,
                ratios,
                (isp_atmo, flow_rate_atmo),
                (isp_vacuum, flow_rate_vacuum),
                v.engine_resources( engine )
            )
