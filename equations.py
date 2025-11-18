import math
import sympy

g0 = 9.81 # : m s^-2

def compute_dv(
        isp, # : s^-1
        m, # : kg
        dm # : kg
): # dv generated : m s^-1

    return g0 * isp * math.log( m / ( m - dm ) )

def compute_dm(
        isp, # : s^-1
        dv, # : m s^-1
        m # kg
): # : kg

    return m * ( 1.0 - 1.0 / math.exp( dv / (isp * g0)) )

def compute_dt(
        isp, # : s^-1
        dv, # : m s^-1
        m, # : kg
        dm_dt, # : kg s^-1
        alpha = 1.0 # : scalar
): # : s
    
    return compute_dm( isp, dv, m ) / ( dm_dt * alpha )

def compute_alpha(
        isp, # : s^-1
        dv, # : m s^-1
        m, # : kg
        dt, # : s
        dm_dt # : kg s^-1
): # scalar

    return compute_dm( isp, dv, m )/ ( dm_dt * dt )

def compute_burning_time(
        dm_dt, # kg s^-1
        ratio, # :scalar = normalized ratio for the resource
        m # :kg = mass available of the resource
): #: s = the time needed to burn all the resource
    return mass / ( dm_dt * ratio )
