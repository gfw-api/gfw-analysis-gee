"""ERRORS"""


class Error(Exception):

    def __init__(self, message):
        self.message = message

    @property
    def serialize(self):
        return {
            'message': self.message
        }


class HansenError(Error):
    pass


class GeodescriberError(Error):
    pass

class NLCDLandcoverError(Error):
    pass
  
class HistogramError(Error):
    pass


class LandcoverError(Error):
    pass


class LandsatTilesError(Error):
    pass


class SentinelTilesError(Error):
    pass


class HighResTilesError(Error):
    pass


class RecentTilesError(Error):
    pass


class CompositeError(Error):
    pass    


class FormaError(Error):
    pass


class WHRCBiomassError(Error):
    pass

class BiomassLossError(Error):
    pass

class MangroveBiomassError(Error):
    pass

class PopulationError(Error):
    pass

class soilCarbonError(Error):
    pass


class GeostoreNotFound(Error):
    pass

class ClassificationError(Error):
    pass
