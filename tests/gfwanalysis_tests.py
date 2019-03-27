import gfwanalysis

def test_serialize_umd():
    d = {'area_ha': 0.0,
         'tree_extent': 0,
         'tree_extent2010': 0,
         'gain': 0,
         'loss': 0
        }
    id_type = 'umd'
    s_obj = gfwanalysis.serializers.serialize_umd(d, id_type)
    assert s_obj.get('type') == id_type
    assert s_obj.get('attributes').get('loss') is not None
