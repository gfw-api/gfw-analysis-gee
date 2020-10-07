from gfwanalysis.serializers import serialize_recent_data
from gfwanalysis.services.analysis.recent_tiles import RecentTiles


def test_serialize_recent_data():
    """Test the Recent Tiles data Serializer."""
    response_data = [{
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
    serialized_object = serialize_recent_data(response_data, id_type)

    assert serialized_object.get('type') == id_type
    assert len(serialized_object.get('tiles', [])) == 2

    serialized_object_attribute = serialized_object.get('tiles')[0].get('attributes')

    assert serialized_object_attribute.get('instrument') == response_data[0]['spacecraft']
    assert serialized_object_attribute.get('source') == response_data[0]['source']
    assert serialized_object_attribute.get('cloud_score') == response_data[0]['cloud_score']
    assert serialized_object_attribute.get('date_time') == response_data[0]['date']
    assert serialized_object_attribute.get('tile_url') == response_data[0]['tile_url']
    assert serialized_object_attribute.get('bbox') == response_data[0]['bbox']
    assert serialized_object_attribute.get('thumbnail_url') == response_data[0]['thumb_url']


def test_recent_data_type():
    """
    Test a known lat, lon iniput gives back expected metadata response.
    """

    # Canaries Test
    lon = -16.644
    lat = 28.266

    start = '2020-01-01'
    end = '2020-02-01'

    kwargs = {'lat': lat, 'lon': lon,
              'start': start, 'end': end, 'sort_by': None}
    method_response = RecentTiles.recent_data(**kwargs)
    first_tile = method_response[0]

    spacecraft_list = ['Sentinel', 'Landsat']

    assert len(method_response) > 1
    assert type(first_tile.get('bbox')) == dict
    assert type(first_tile.get('source')) == str
    assert 0 <= first_tile.get('cloud_score') <= 100
    assert type(first_tile.get('spacecraft')) == str
    assert any([spacecraft in first_tile.get('spacecraft') for spacecraft in spacecraft_list])
    assert type(first_tile.get('date')) == str


def test_recent_tile_url():
    """
    Test a known source returns expected tile url.
    """

    col_data = {'source': 'COPERNICUS/S2/20200530T115219_20200530T115220_T28RCS'}

    kwargs = {  
        'col_data': col_data,
        'bands':None,
        'bmin':None,
        'bmax':None,
        'opacity':None
    }

    method_response = RecentTiles.recent_tiles(**kwargs)
    tile_url = method_response.get('tile_url', '')
    source = method_response.get('source', '')
    
    assert 'source' in method_response
    assert source in col_data['source']
    assert 'tile_url' in method_response
    assert 'https://earthengine.googleapis.com/v1alpha/projects/earthengine-legacy/maps/' in tile_url
