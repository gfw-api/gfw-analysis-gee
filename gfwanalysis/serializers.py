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


def serialize_forma(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'areaHa': analysis.get('area_ha', None),
            'alert_counts': analysis.get('alert_counts', None)
        }
    }
