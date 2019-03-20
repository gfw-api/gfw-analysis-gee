"""CLASSIFICATION SERVICE"""

import logging

import ee
from gfwanalysis.errors import ClassificationError
from gfwanalysis.config import SETTINGS
import pickle

class ClassificationService(object):

    @staticmethod
    def classify(img_id):
        """
        For a given area classify the forest amount and return a image with the classified forest and amount.
            example of a valid img_id = 'COPERNICUS/S2/20181222T115211_20181222T115210_T28RCS'
        """
        logging.info(f'[classification_service]: img_id={img_id}')
        try:
            # If one exists restore it from local storage
            model = get_model_from_local() 
            if(model == None):
                # If none exists in local storage restore from google storage
                logging.info(f"[classification_service]: model not found locally!")
                model = get_model_from_bucket()
                if(model == None):
                    # If none exists in google storage create one (and add it to local and remote storage)
                    #model = create_model()
                    pass

            # grab the image specified by the ID
            image = get_image(img_id)
            # Apply classifer to specified L8 or S2 image
            #logging.info(f"[classification_service]: classified version = {classified_image}")
            
            # Generate tile url and return in d['url'] object
            url = get_url_classify_image(image, model) #(classified_image)
            logging.info(f'[classification_service]: passed main logic url={url}')
            d = {}
            d['url'] = url
            return d
        except Exception as error:
            logging.error(str(error))
            raise ClassificationError(message='Error in Classification Analysis')


def get_url_classify_image(image, model):
    logging.info(f'[classification_service]: attempting to get url')
    viz = {'min': 0, 'max': 3, 'palette': ['yellow', 'blue', 'grey', 'green']}
    d = image.select("B4","B3","B2").divide(10000).classify(model).getMapId(viz)
    logging.info(f'[classification_service]: d object = {d}')
    base_url = 'https://earthengine.googleapis.com'
    url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
    return url

def create_model():
    logging.info(f'[classification_service]: attempting to create model')
    try:
        # find a way of checking if model is in local memory (probably using OS?)
        return ""
    except:
        return None

def get_image(img_id):
    """Check if S2 or L8 image and treat image accordingly"""
    logging.info(f'[classification_service]: attempting to get image {img_id}')
    try:
        result_img = ee.Image(img_id)
        #logging.info(f'[classification_service]: attempting to get image {result_img.getInfo()}')
        return result_img
    except:
        return None

def get_model_from_local():
    try:
        # find a way of checking if model is in local memory (probably using OS?)
        # use OS to test if model is saved as a local file
        model = pickle.load(open("/opt/gfwanalysis/classifier.pkl", 'rb'))       #hardcoded for now
        return model
    except:
        return None

def get_model_from_bucket():
    logging.info(f'[classification_service]: attempting to get model from bucket')
    bucket_name = 'skydipper_materials'
    source_blob_name = 'classifier.pkl'
    destination_file_name = '/opt/downl_classif.pkl'
    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        print('Blob {} downloaded to {}.'.format(source_blob_name,destination_file_name))
        loaded_model = joblib.load("/opt/downl_classif.pkl")             #careful to change path when loading locally according to where it was downloaded
        return loaded_model
    except:
        return None