from enum import Enum

#####

def version():
    return "0.0.1"

#####


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

