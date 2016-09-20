import os.path
from oauth2client.service_account import ServiceAccountCredentials
from ee import oauth

# The URL of the Earth Engine API.
EE_URL = 'https://earthengine.googleapis.com'

# The service account email address authorized by your Google contact.
EE_ACCOUNT= '390573081381-lm51tabsc8q8b33ik497hc66qcmbj11d@developer.gserviceaccount.com'
#'gfw-apis@appspot.gserviceaccount.com'

# The private key associated with your service account in Privacy Enhanced
# Email format (.pem suffix).  To convert a private key from the RSA format
# (.p12 suffix) to .pem, run the openssl command like this:
# openssl pkcs12 -in downloaded-privatekey.p12 -nodes -nocerts > privatekey.pem
##print os.path.abspath()
EE_PRIVATE_KEY_FILE = os.path.abspath(os.path.join('src', os.pardir))+'/privatekey.pem'

##EE_CREDENTIALS = ee.ServiceAccountCredentials(EE_ACCOUNT, EE_PRIVATE_KEY_FILE)

authorization = ServiceAccountCredentials.from_p12_keyfile(EE_ACCOUNT, EE_PRIVATE_KEY_FILE, scopes=oauth.SCOPE)
