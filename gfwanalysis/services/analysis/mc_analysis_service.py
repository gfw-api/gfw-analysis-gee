"""MC ANALYSIS SERVICE"""

import ee
import logging
import pandas as pd
from gfwanalysis.errors import MCAnalysisError


class MCAnalysisService(object):

    @staticmethod
    def analyze(timeseries, window, bin_number, mc_number):
        """This is the Monte Carlo Analysis Service
        """
        if not window:
            window = 5
        if not bin_number:
            bin_number = 100
        if not mc_number:
            mc_number = 1000
        logging.info(f"[MC Service] {timeseries}, {window}, {bin_number}, {mc_number}")
        logging.info(f"[MC service] pandas: {pd.__version__}")
        d={}
        d["window"]=window
        d["bin_number"]=bin_number
        d["mc_number"]=mc_number
        return d