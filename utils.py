import krpc
import prelude

def parts_in_stage( vessel, stage, categories ):

        parts = [
            part
            for part in vessel.parts.all
            if part.decouple_stage < stage and part.stage == stage
        ]

        res = dict(
            [ ( category, list() ) for category in categories ]
        )

        for part in parts:
            cats = [
                category
                for category in categories
                if part.__getattribute__( category ) is not None
            ]
            if len(cats) != 0:
                res[ cats[0] ].append( part )
            
def crossfeed_closure( part ):

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

    return cross_fueled_next_parts
