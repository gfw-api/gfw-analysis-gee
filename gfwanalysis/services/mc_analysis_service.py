"""MC ANALYSIS SERVICE"""

import ee
import logging

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import MCAnalysisError



class MCAnalysisService(object):

    @staticmethod
    def analyze(timeseries, window=5, bin_number=100, mc_number=1000):
        """This is the Monte Carlo Analysis Service
        """
        logging.info(f"[MCService] {timeseries}, {window}, {bin_number}, {mc_number}")
        d={}
        d["window"]=window
        d["bin_number"]=bin_number
        d["mc_number"]=mc_number
        return d