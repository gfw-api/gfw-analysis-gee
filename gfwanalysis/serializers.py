"""Serializers"""


def serialize_umd(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'loss': analysis.get('loss', None),
            'gain': analysis.get('gain', None),
            'treeExtent': analysis.get('tree_extent', None),
            'areaHa': analysis.get('area_ha', None),
        }
    }


def serialize_histogram(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'histogram': analysis.get('result', None),
            'areaHa': analysis.get('area_ha', None),
        }
    }

def serialize_landcover(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'landcover': analysis.get('result', None),
            'areaHa': analysis.get('area_ha', None),
        }
    }


def serialize_forma(analysis, type):
    """Convert the output of the forma250 analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'areaHa': analysis.get('area_ha', None),
            'areaHaLoss': analysis.get('area_ha_loss', None),
            'alertCounts': analysis.get('alert_counts', None)
        }
    }

def serialize_biomass(analysis, type):
    """Convert the output of the biomass_loss analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'biomass': analysis.get('biomass', None),
            'biomassLoss': analysis.get('biomass_loss', None),
            'biomassLossByYear': analysis.get('biomass_loss_by_year', None),
            'cLossByYear': analysis.get('c_loss_by_year', None),
            'co2LossByYear': analysis.get('co2_loss_by_year', None),
            'treeLossByYear': analysis.get('tree_loss_by_year', None),
            'areaHa': analysis.get('area_ha', None)
        }
    }

def serialize_landsat_url(analysis, type):
    """Convert output of landsat_tiles to json"""
    return {
        'id': None,
        'type': type,
        'attributes':{
            "url": analysis.get('url', None)
            }
        }
