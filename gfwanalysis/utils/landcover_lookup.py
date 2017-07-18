import logging


def lookup(layer, result_dict):

    lkp = get_lookup(layer)

    return add_landcover_names(result_dict, lkp)

def valid_lulc_codes(layer):

    return [int(x) for x in get_lookup(layer).keys()]

def get_lookup(layer):

    all_lulc_dict = {
    'globcover': {
        '11': 'Post-flooding or irrigated croplands',
        '14': 'Rainfed croplands',
        '20': 'Mosaic Cropland (50-70%) / Vegetation (grassland, shrubland, forest) (20-50%)',
        '30': 'Mosaic Vegetation (grassland, shrubland, forest) (50-70%) / Cropland (20-50%)',
        '40': 'Closed to open (>15%) broadleaved evergreen and/or semi-deciduous forest (>5m)',
        '50': 'Closed (>40%) broadleaved deciduous forest (>5m)',
        '60': 'Open (15-40%) broadleaved deciduous forest (>5m)',
        '70': 'Closed (>40%) needleleaved evergreen forest (>5m)',
        '90': 'Open (15-40%) needleleaved deciduous or evergreen forest (>5m)',
        '100': 'Closed to open (>15%) mixed broadleaved and needleleaved forest (>5m)',
        '110': 'Mosaic Forest/Shrubland (50-70%) / Grassland (20-50%)',
        '120': 'Mosaic Grassland (50-70%) / Forest/Shrubland (20-50%)',
        '130': 'Closed to open (>15%) shrubland (<5m)',
        '140': 'Closed to open (>15%) grassland',
        '150': 'Sparse (>15%) vegetation (woody vegetation, shrubs, grassland)',
        '160': 'Closed (>40%) broadleaved forest regularly flooded - Fresh water',
        '170': 'Closed (>40%) broadleaved semi-deciduous and/or evergreen forest regularly flooded - Saline water',
        '180': 'Closed to open (>15%) vegetation (grassland, shrubland, woody vegetation) on regularly flooded or waterlogged soil - Fresh, brackish or saline water',
        '190': 'Artificial surfaces and associated areas (urban areas >50%) GLOBCOVER 2009',
        '200': 'Bare areas',
        '210': 'Water bodies',
        '220': 'Permanent snow and ice',
        '230': 'Unclassified'
        },

    'foraf':  {
        '1': 'Dense moist forest',
        '2': 'Submontane forest',
        '3': 'Mountain forest',
        '4': 'Edaphic forest',
        '5': 'Mangrove',
        '6': 'Forest-savanna mosaic',
        '7': 'Rural complex and young secondary forest',
        '8': 'Closed to open deciduous woodland',
        '9': 'Savanna woodland-Tree savanna',
        '10': 'Shrubland',
        '11': 'Grassland',
        '12': 'Aquatic grassland',
        '13': 'Swamp grassland',
        '14': 'Sparse vegetation',
        '15': 'Mosaic cultivated areas/vegeatation( herbaceous or shrub)',
        '16': 'Agriculture',
        '17': 'Irrigated agriculture',
        '18': 'Bare areas',
        '19': 'Artificial surfaces and associated areas',
        '20': 'Water Bodies'
        },

    'liberia':  {
        '0': 'NoData',
        '1': 'Forest >80%',
        '2': 'Forest 30 - 80%',
        '3': 'Forest <30%',
        '4': 'Mangrove & Swamps',
        '5': 'Settlements',
        '7': 'Surface Water Bodies',
        '8': 'Grassland',
        '9': 'Shrub',
        '10': 'Bare soil',
        '11': 'Ecosystem complex (rock & sand)',
        '25': 'Clouds'
        }
    }

    return all_lulc_dict[layer]

def add_landcover_names(result_dict, lkp):

    output_dict = {}
    print('adding landcover names')

    for key, val in result_dict.items():
        logging.info(key, val)
        landcover_name = lkp[key]
        output_dict[key] = {'pixelCount': val, 'landcover': landcover_name}

    return output_dict
