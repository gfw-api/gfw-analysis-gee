from gfwanalysis.serializers import serialize_recent_url, serialize_recent_data
from gfwanalysis.services.analysis.recent_tiles import RecentTiles


def test_serialize_recent_tiles_data():
    """Test the Recent Tiles data Serializer."""
    d = [{
        'spacecraft': 'a1',
        'source': 'a2',
        'cloud_score': 'a3',
        'date': 'a4',
        'tile_url': 'a5',
        'thumb_url': 'a6',
        'bbox': 'a7'
    }, {
        'spacecraft': 'b1',
        'source': 'b2',
        'cloud_score': 'b3',
        'date': 'b4',
        'tile_url': 'b5',
        'thumb_url': 'b6',
        'bbox': 'b7'
    }]

    id_type = 'recent_tiles_data'
    s_obj = serialize_recent_data(d, id_type)
    assert s_obj.get('type') == id_type
    assert len(s_obj.get('tiles', [])) == 2
    assert s_obj.get('tiles')[0].get('attributes').get(
        'instrument') == d[0]['spacecraft']
    assert s_obj.get('tiles')[0].get(
        'attributes').get('source') == d[0]['source']
    assert s_obj.get('tiles')[0].get('attributes').get(
        'cloud_score') == d[0]['cloud_score']
    assert s_obj.get('tiles')[0].get(
        'attributes').get('date_time') == d[0]['date']
    assert s_obj.get('tiles')[0].get('attributes').get(
        'tile_url') == d[0]['tile_url']
    assert s_obj.get('tiles')[0].get('attributes').get('bbox') == d[0]['bbox']
    assert s_obj.get('tiles')[0].get('attributes').get(
        'thumbnail_url') == d[0]['thumb_url']


def test_recent_tile_data_type():
    """
    Test a known region gives back expected types.
    """

    # Canaries Test
    lon = -16.644
    lat = 28.266

    start = '2020-01-01'
    end = '2020-02-01'

    kwargs = {'lat': lat, 'lon': lon,
              'start': start, 'end': end, 'sort_by': None}
    method_response = RecentTiles.recent_data(**kwargs)

    spacecraft = ['COPERNICUS', 'LANDSAT']
    assert len(method_response) > 1
    assert type(method_response[0].get('bbox')) == dict
    assert type(method_response[0].get('source')) == str
    assert 0 <= method_response[0].get('cloud_score') <= 100
    assert type(method_response[0].get('spacecraft')) == str
    assert any([s in method_response[0].get('spacecraft') for s in spacecraft])
    assert type(method_response[0].get('date')) == str
