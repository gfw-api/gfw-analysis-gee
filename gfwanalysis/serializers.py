"""Serializers"""
import logging


def serialize_umd(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'loss': analysis.get('loss', None),
            'gain': analysis.get('gain', None),
            'treeExtent': analysis.get('treeExtent', None),
            'treeExtent2010': analysis.get('treeExtent2010', None),
            'areaHa': analysis.get('area_ha', None),
            'loss_start_year': analysis.get('loss_start_year', None),
            'loss_end_year': analysis.get('loss_end_year', None)
        }
    }


def serialize_mc(analysis, type):
    """serialised function for the Monte Carlo Analysis"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'window': analysis.get('window', None),
            'mc_number': analysis.get('mc_number', None),
            'bin_number': analysis.get('bin_number', None),
            'description': analysis.get('description', None),
            'anomaly': analysis.get('anomaly', None),
            'anomaly_uncertainty': analysis.get('anomaly_uncertainty', None),
            'upper_p': analysis.get('upper_p', None),
            'p': analysis.get('p', None),
            'lower_p': analysis.get('lower_p', None)

        }
    }


def serialize_classifier_output(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'url': analysis.get('url', None)
        }
    }


def serialize_composite_output(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'thumb_url': analysis.get('thumb_url', None),
            'tile_url': analysis.get('tile_url', None),
            'dem': analysis.get('dem', None),
            'zonal_stats': analysis.get('zonal_stats', None)
        }
    }


def serialize_table_umd(analysis, type):
    """ Convert the aggregate_values=false Hansen response into a table"""
    rows = []
    for year in analysis.get('loss', None):
        rows.append({'year': year,
                     'loss': analysis.get('loss', None).get(year),
                     'gain': analysis.get('gain', None),
                     'areaHa': analysis.get('area_ha', None),
                     'treeExtent': analysis.get('treeExtent', None),
                     'treeExtent2010': analysis.get('treeExtent2010', None),
                     })
    return {
        'id': None,
        'type': type,
        'attributes': rows
    }


def serialize_population(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'totalPopulation': analysis.get('population', None).get('population_count', None),
            'populationDensity': float(f"{analysis.get('population_density'):3.2f}"),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_mangrove_biomass(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'total': analysis.get('biomass', None).get('b1', None),
            'biomassDensity': int(analysis.get('biomass_density')),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_whrc_biomass(analysis, type):
    """."""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'totalBiomass': analysis.get('biomass', None),
            'biomassDensity': int(analysis.get('biomass_density')),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_soil_carbon(analysis, type):
    """Return serialised soil carbon data"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'total_soil_carbon': analysis.get('total_soil_carbon', None).get('b1_first', None),
            'soil_carbon_density': int(analysis.get('soil_carbon_density', None)),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_histogram(analysis, type):
    """."""

    return {
        'id': None,
        'type': type,
        'attributes': {
            'histogram': analysis.get('result', None),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_landcover(analysis, type):
    """."""

    return {
        'id': None,
        'type': type,
        'attributes': {
            'landcover': analysis.get('result', None),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_forma(analysis, type):
    """Convert the output of the forma250 analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'areaHa': analysis.get('area_ha', None),
            'areaHaLoss': analysis.get('area_ha_loss', None),
            'alertCounts': analysis.get('alert_counts', None)
        }
    }


def serialize_forma_latest(analysis, type):
    """Convert the output of the forma250 analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'latest': analysis.get('latest', None)
        }
    }


def serialize_biomass_v1(analysis, type):
    """Convert the output of the biomass_loss analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'biomass': analysis.get('biomass', None),
            'biomassLoss': analysis.get('biomass_loss', None),
            'biomassLossByYear': analysis.get('biomass_loss_by_year', None),
            'cLossByYear': analysis.get('c_loss_by_year', None),
            'co2LossByYear': analysis.get('co2_loss_by_year', None),
            'treeLossByYear': analysis.get('tree_loss_by_year', None),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_biomass_table_v1(analysis, type):
    """Convert the output of the biomass_loss analysis to json"""
    rows = []
    for year in analysis.get('biomass_loss_by_year'):
        rows.append({'year': year,
                     'biomassLossByYear': analysis.get('biomass_loss_by_year', None).get(year, None),
                     'totalBiomass': analysis.get('biomass', None),
                     'cLossByYear': analysis.get('c_loss_by_year', None).get(year, None),
                     'co2LossByYear': analysis.get('co2_loss_by_year', None).get(year, None),
                     'treeLossByYear': analysis.get('tree_loss_by_year', None).get(year, None),
                     'totalAreaHa': analysis.get('area_ha', None),
                     })
    return {
        'id': None,
        'type': type,
        'attributes': rows
    }


def serialize_nlcd_landcover_v2(analysis, type):
    """Convert the output of the biomass_loss analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': analysis
    }


def serialize_biomass_v2(analysis, type):
    """Convert the output of the biomass_loss analysis to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            'biomassLoss': analysis.get('biomassLoss', None),
            'biomassLossByYear': analysis.get('biomassLossByYear', None),
            'cLossByYear': analysis.get('cLossByYear', None),
            'co2LossByYear': analysis.get('co2LossByYear', None),
            'areaHa': analysis.get('area_ha', None)
        }
    }


def serialize_biomass_table_v2(analysis, type):
    """Convert the output of the biomass_loss analysis to json"""
    rows = []
    for year in analysis.get('biomassLossByYear'):
        rows.append({'year': year, 'biomassLossByYear': analysis.get('biomassLossByYear', None).get(year, None),
                     'cLossByYear': analysis.get('cLossByYear', None).get(year, None),
                     'co2LossByYear': analysis.get('co2LossByYear', None).get(year, None),
                     'areaHa': analysis.get('area_ha', None)
                     })
    return {
        'id': None,
        'type': type,
        'attributes': rows
    }


def serialize_landsat_url(analysis, type):
    """Convert output of landsat_tiles to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            "url": analysis.get('url', None)
        }
    }


def serialize_sentinel_url(analysis, type):
    """Convert output of landsat_tiles to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            "url_image": analysis.get('image_tiles', None),
            "url_boundary": analysis.get('boundary_tiles', None),
            "date_time": analysis.get('metadata', None).get('date_time', None),
            "product_id": analysis.get('metadata', None).get('product_id', None)
        }
    }


def serialize_sentinel_mosaic(analysis, type):
    """Convert output of landsat_tiles to json"""
    return {
        'id': None,
        'type': type,
        'attributes': {
            "tile_url": analysis.get('tile_url', None),
            "thumbnail_url": analysis.get('thumb_url', None),
            "bbox": analysis.get('bbox', None),
        }
    }


def serialize_highres_url(analysis, type):
    """Convert output of images to json"""
    output = []

    for e in range(0, len(analysis)):
        temp_output = {
            'id': None,
            'type': type,
            'attributes': {
                'source': analysis[e].get('metadata', None).get('source', None),
                'cloud_score': analysis[e].get('metadata', None).get('cloud_score', None),
                'date_time': analysis[e].get('metadata', None).get('date_time', None),
                'metadata': analysis[e].get('metadata', None),
                'tile_url': analysis[e].get('tile_url', None),
                'thumbnail_url': analysis[e].get('thumbnail_url', None),
                'boundary_tiles': analysis[e].get('boundary_tiles', None)
            }
        }
        output.append(temp_output)

    return output


def serialize_recent_data(analysis, type):
    logging.info("[SERIALIZER] initiating...")
    """Convert output of images to json"""
    output = []

    for e in range(0, len(analysis)):
        temp_output = {
            'attributes': {
                'instrument': analysis[e].get('spacecraft', None),
                'source': analysis[e].get('source', None),
                'cloud_score': analysis[e].get('cloud_score', None),
                'date_time': analysis[e].get('date', None),
                'tile_url': analysis[e].get('tile_url', None),
                'thumbnail_url': analysis[e].get('thumb_url', None),
                'bbox': analysis[e].get('bbox', None)
            }
        }
        output.append(temp_output)
    return {
        'tiles': output,
        'id': None,
        'type': type
    }


def serialize_recent_url(analysis, type):
    logging.info("[SERIALISER] Initiating")
    """Convert output of images to json"""
    tmp_output = []
    output = {}

    if type == 'recent_thumbs_url':

        output['id'] = None
        output['type'] = type

        for e in range(0, len(analysis)):
            temp_obj = {
                'source': analysis[e].get('source', None),
                'thumbnail_url': analysis[e].get('thumb_url', None)
            }
            tmp_output.append(temp_obj)
        output['attributes'] = tmp_output

    elif type == 'recent_tiles_url':

        output['id'] = None
        output['type'] = type

        for e in range(0, len(analysis)):
            temp_obj = {
                'source_id': analysis[e].get('source', None),
                'tile_url': analysis[e].get('tile_url', None)
            }
            tmp_output.append(temp_obj)
        output['attributes'] = tmp_output

    return output
