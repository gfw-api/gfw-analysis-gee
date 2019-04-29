import logging

from gfwanalysis.serializers import serialize_umd
from gfwanalysis.services.analysis.hansen_service import HansenService

def test_serialize_umd():
    """Test the Hansen Serializer."""
    d = {'area_ha': 0.0,
         'tree_extent': 0,
         'tree_extent2010': 0,
         'gain': 0,
         'loss': 0
        }
    id_type = 'umd'
    s_obj = serialize_umd(d, id_type)
    assert s_obj.get('type') == id_type
    assert s_obj.get('attributes').get('loss') is not None

def test_known_area_loss():
    """
    Test a known region gives back specific values within a given tolerance
        for the hansen geostore analysis between 2001 and 2018 at threshold=30.
    """
    geojson = {'features': [{'properties': None,
                'type': 'Feature',
                'geometry': {'type': 'Polygon',
                    'coordinates': [[[-0.5712890625, 51.2619148530845],
                    [0.3515625, 51.2619148530845],
                    [0.3515625, 51.6861795485562],
                    [-0.5712890625, 51.6861795485562],
                    [-0.5712890625, 51.2619148530845]]]}}],
                'crs': {},
                'type': 'FeatureCollection'}
    kwargs = {'geojson': geojson, 'threshold':30, 'begin':'2001-01-01', 'end':'2018-12-31'}
    method_response = HansenService.analyze(**kwargs)
    #logging.info(f'[Test]: umd d={method_response}')
    verify = {'loss_start_year': 1,
                'loss_end_year': 18,
                'tree_extent': 47223.84,
                'tree_extent2010': 51725.06,
                'gain': 1102.2,
                'loss': 322.96}
    assert method_response.get('tree_extent') == verify.get('tree_extent')
    assert method_response.get('tree_extent2010') == verify.get('tree_extent2010')
    assert method_response.get('gain') == verify.get('gain')
    assert method_response.get('loss') == verify.get('loss')
