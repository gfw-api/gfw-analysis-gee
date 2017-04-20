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
            'hansen': 'projects/wri-datalab/HansenComposite_14-15'
        }
    },
    'carto': {
        'service_account': os.getenv('CARTODB_USER'),
        'uri': 'carto.com/api/v2/sql'
    }
}
