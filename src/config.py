import ee
import httplib2

EE_URL = 'https://earthengine.googleapis.com'
EE_ACCOUNT= '390573081381-lm51tabsc8q8b33ik497hc66qcmbj11d@developer.gserviceaccount.com'
EE_PRIVATE_KEY_FILE = 'private.pem'

EE_CREDENTIALS = ee.ServiceAccountCredentials(EE_ACCOUNT, EE_PRIVATE_KEY_FILE)

http = httplib2.Http()
self.http = credentials.authorize(http)
