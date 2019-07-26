"""MC ANALYSIS SERVICE"""

import ee
import logging
import pandas as pd
import numpy as np
from gfwanalysis.errors import MCAnalysisError
import random
import scipy.stats as stats


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
        #logging.info(f"[MC Service] {timeseries}, {window}, {bin_number}, {mc_number}")
        #logging.info(f"[MC service] pandas: {pd.__version__}")
        #logging.info(f"[MC service] window: {type(window)}")
        d={}
        d["window"]=window
        d["bin_number"]=bin_number
        d["mc_number"]=mc_number
        df = pd.DataFrame(list(timeseries.values()), index= list(timeseries.keys()), columns = ["carbon_emissions"])
        boxcar = df.rolling(window=window, min_periods=window, win_type="boxcar", center=True).mean()
        t0_sigma=np.std(df.values[0:window])
        logging.info(f"[MC service] pandas: {t0_sigma}")
        tn_sigma=np.std(df.values[-window:])
        #logging.info(f"[MC service] pandas: {tn_sigma}")
        cumulative_sigma = np.sqrt(t0_sigma**2 + tn_sigma**2)
        #logging.info(f"[MC service] pandas: {cumulative_sigma}")
        boxcar_values = boxcar.carbon_emissions.values
        mask = np.isnan(boxcar_values)
        cleaned_boxcar_values = boxcar_values[mask != True]
        t0 = cleaned_boxcar_values[0]
        #logging.info(f"[MC service] pandas: {t0}")
        tn = cleaned_boxcar_values[-1]
        #logging.info(f"[MC service] pandas: {tn}")
        anomaly = tn - t0
        #logging.info(f"[MC service] pandas: {anomaly}")

        # Build the Monte Carlo distribution (null cases)
        values = list(df.values.flatten())
        #logging.info(f"[MC service] pandas: {values}")

        mc_pop = []
        for draw in range(mc_number):
            tmp_mean1 = np.array(random.choices(population=values, k=window)).mean()
            tmp_mean2 = np.array(random.choices(population=values, k=window)).mean()
            tmp_anom = tmp_mean1 - tmp_mean2
            mc_pop.append(tmp_anom)

        hist = np.histogram(mc_pop, bins=bin_number)
        bins = hist[1]
        density = hist[0] / hist[0].sum()
        step = (bins[1] - bins[0])
        bcenter = [bpos + step for bpos in bins[:-1]]

        #Gaus fit

        mu, sigma = np.mean(mc_pop), np.std(mc_pop)
        #logging.info(f"[MC service] pandas: {mu}")
        #logging.info(f"[MC service] pandas: {sigma}")
        ygauss = stats.norm.pdf(bins, mu, sigma) # a function from matplotlib.mlab.
        #logging.info(f"[MC service] ygauss: {ygauss}")
        ynormgauss = ygauss/sum(ygauss) # Normalize distribution so sum is 1.0
        #logging.info(f"[MC service] ynormgauss: {ynormgauss}")
        results = MCAnalysisService.integrate_fits(anomaly=anomaly, mu=mu, sigma=sigma, anomaly_uncertainty=cumulative_sigma)
        #logging.info(f"[MC service] results: {results}")
        return results

    
    @staticmethod
    def integrate_fits(anomaly, mu, sigma, anomaly_uncertainty=None):
        """
        Use a CDF of the Gaussian distribution to estimate probability.
        """
        results = {}
        upper_p = None
        lower_p = None
        # anomaly p-value
        cdf_value = stats.norm.cdf(anomaly, mu, sigma)
        # anomaly ±uncertainty p values
        if anomaly_uncertainty:
            upper_p = stats.norm.cdf(anomaly_uncertainty + anomaly, mu, sigma)
            lower_p = stats.norm.cdf(anomaly - anomaly_uncertainty, mu, sigma)    
        p_val = 1 - cdf_value
        if anomaly > 0: 
            change = 'Increase'
        else:
            change = 'Decrease'
        
        results['description'] = (f"""{change} of {anomaly:.2g} CO₂e over observation period has an associated p-value of {p_val:3.3f}"""
                                f"""± {upper_p:3.3f} {lower_p:3.3f}.""")
        results['anomaly'] = anomaly
        results['anomaly_uncertainty'] = anomaly_uncertainty
        results['upper_p'] = upper_p
        results['p'] = cdf_value
        results['lower_p'] = lower_p
        return results