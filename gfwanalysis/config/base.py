"""-"""

import os
from gfwanalysis.utils.files import BASE_DIR


SETTINGS = {
    'logging': {
        'level': 'DEBUG'
    },
    'service': {
        'port': 4500
    },
    'gee': {
        'service_account': '390573081381-lm51tabsc8q8b33ik497hc66qcmbj11d@developer.gserviceaccount.com',
        'privatekey_file': BASE_DIR + '/privatekey.pem',
        'assets': {
            'hansen': 'projects/wri-datalab/HansenComposite_16',
            'globcover': 'ESA/GLOBCOVER_L4_200901_200912_V2_3',
            'foraf': 'projects/wri-datalab/gfw-api/central-africa_veg_foraf',
            'liberia': 'projects/wri-datalab/gfw-api/lbr-landcover',
            'ifl2000': 'projects/wri-datalab/gfw-api/ifl-world',
            'mangroves': 'LANDSAT/MANGROVE_FORESTS/2000',
            'forma250GFW': 'projects/wri-datalab/FORMA250',
            'biomassloss': {
                'hansen_loss_thresh': 'HANSEN/gfw_loss_by_year_threshold_2015',
                'biomass_2000': 'users/davethau/whrc_carbon_test/carbon'
            }
        },
        'lulc_band': {
            'globcover': 'landcover',
            'mangroves': '1'
        }
    },
    'carto': {
        'service_account': os.getenv('CARTODB_USER'),
        'uri': 'carto.com/api/v2/sql'
    }
}
