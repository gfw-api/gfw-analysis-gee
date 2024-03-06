import collections
import logging

import ee

from gfwanalysis.config import SETTINGS

collections.Callable = collections.abc.Callable


# Initializing GEE
gee = SETTINGS.get("gee")
ee_user = gee.get("service_account")
private_key_file = gee.get("privatekey_file")
if private_key_file:
    logging.info(
        f"Initializing EE with privatekey.json credential file: {ee_user} | {private_key_file}"
    )
    credentials = ee.ServiceAccountCredentials(ee_user, private_key_file)
    ee.Initialize(credentials)
    ee.data.setDeadline(60000)
else:
    raise ValueError("privatekey.json file not found. Unable to authenticate EE.")
