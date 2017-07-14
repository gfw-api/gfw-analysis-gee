


def lookup(landcover_type, result_dict):

    if landcover_type == 'globcover':
        lkp = globcover()

    else:
        raise ValueError('Unknown landcover type {}'.format(landcover_type))

    return add_landcover_names(result_dict, lkp)


def globcover():

    lkp = {
    '11': 'Post-flooding or irrigated croplands (or aquatic)',
    '14': 'Rainfed croplands',
    '20': 'Mosaic cropland (50-70%) / vegetation (grassland/shrubland/forest) (20-50%)',
    '30': 'Mosaic vegetation (grassland/shrubland/forest) (50-70%) / cropland (20-50%)',
    '40': 'Closed to open (>15%) broadleaved evergreen or semi-deciduous forest (>5m)',
    '50': 'Closed (>40%) broadleaved deciduous forest (>5m)',
    '60': 'Open (15-40%) broadleaved deciduous forest/woodland (>5m)',
    '70': 'Closed (>40%) needleleaved evergreen forest (>5m)',
    '90': 'Open (15-40%) needleleaved deciduous or evergreen forest (>5m)',
    '100': 'Mosaic forest or shrubland (50-70%) / grassland (20-50%)',
    '110': 'Mosaic forest or shrubland (50-70%) / grassland (20-50%)',
    '120': 'Mosaic grassland (50-70%) / forest or shrubland (20-50%)',
    '130': 'Closed to open (>15%) (broadleaved or needleleaved evergreen or deciduous) shrubland (<5m)',
    '140': 'Closed to open (>15%) herbaceous vegetation (grassland savannas or lichens/mosses)',
    '150': 'Closed to open (>15%) herbaceous vegetation (grassland savannas or lichens/mosses)',
    '160': 'Closed to open (>15%) broadleaved forest regularly flooded (semi-permanently or temporarily) - Fresh or brackish water',
    '170': 'Closed (>40%) broadleaved forest or shrubland permanently flooded - Saline or brackish water',
    '180': 'Closed to open (>15%) grassland or woody vegetation on regularly flooded or waterlogged soil -  Fresh brackish or saline water',
    '190': 'Artificial surfaces and associated areas (Urban areas >50%)',
    '200': 'Bare areas',
    '210': 'Water bodies',
    '220': 'Permanent snow and ice',
    '230': 'No Data'}

    return lkp

def add_landcover_names(result_dict, lkp):

    output_dict = {}
    print('adding landcover names')

    for key, val in result_dict.items():
        print(key, val)
        landcover_name = lkp[key]
        output_dict[key] = {'pixelCount': val, 'landcover': landcover_name}

    return output_dict
