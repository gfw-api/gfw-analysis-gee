"""CLASSIFICATION SERVICE"""

import logging

import ee
from gfwanalysis.errors import ClassificationError
from gfwanalysis.config import SETTINGS


class ClassificationService(object):

    @staticmethod
    def classify(img_id):
        """For a given area classify the forest amount and return a image with the classified forest and amount."""
        logging.info(f'[classification_service]: img_id={img_id}')
        try:
            d = {}
            d['url'] = "testString"
            return d
        except Exception as error:
            logging.error(str(error))
            raise ClassificationError(message='Error in Classification Analysis')