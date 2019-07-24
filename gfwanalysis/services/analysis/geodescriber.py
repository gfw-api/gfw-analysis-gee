import logging
from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import GeodescriberError
from gfwanalysis.utils.geo import get_region, human_format, reverse_geocode_a_geostore, check_equivence
from googletrans import Translator
import ee
import json
import asyncio
from shapely.geometry import shape

class GeodescriberService(object):

    @staticmethod
    def create_title_elements(s):
        """Take revsere geocoding results for upper and lower corners of a polygons bounds,
            Extract the region, county, country, continent attributes of the locations.
            Use the overlap to set an appropriate title.
        """
        loop = asyncio.new_event_loop()
        func = reverse_geocode_a_geostore(loop, s)
        geocode_results = loop.run_until_complete(func)

        parsed_results = []
        
        for result in geocode_results:
            if result:
                temp_json= result.geojson.get('features')[0].get('properties')  
            else:
                temp_json = {}

        # Filtering out the locations we care about
            parsed_results.append(
                {
                    'country': temp_json.get('country', None), 
                    'county': temp_json.get('county', None), 
                    'region': temp_json.get('region', None), 
                    'continent': continent_lookup[iso_to_continent[temp_json.get('country_code', '').upper()]]}
                )

        #Getting the data structure
    
            title_dict = {
                'country':[] ,
                'county': [],
                'continent': [],
                'region': []
            }
            
        for key in title_dict.keys():
            for item in parsed_results:
                value = item[key]
                title_dict[key].append(value)

        return title_dict

    @staticmethod
    def create_title(title_elements, land_sea):
        tmp_config = {'items': {}, 'sentence': ""}
       
        truth_dict ={
            'country':None,
            'county': None,
            'continent': None,
            'region': None
        } 

        distinct_locs ={
            'country':[],
            'county': [],
            'continent': [],
            'region': []
        } 
    
        # Create the title based on the thruth dictionary
        for key,value in title_elements.items():
            locs = [v for v in value if v is not None]
            distinct_locs[key] = locs
            truth_dict[key] = len(set(locs)) == 1

        country_list = distinct_locs['country']
        county_list = distinct_locs['county']
        continent_list = distinct_locs['continent']
        region_list = distinct_locs['region']

        if land_sea: land_sea_phrase = f'{land_sea} area'
        else: land_sea_phrase = 'Area'

        if all([val == True for val in truth_dict.values()]):
            # If all points in the same Continents, Country, Region, and County
            tmp_config['sentence'] = '{ttl_0} in {ttl_1}, {ttl_2}, {ttl_3}'
            tmp_config['items'] = {'ttl_0': land_sea_phrase, 'ttl_1': county_list[0], 'ttl_2': region_list[0], 'ttl_3': country_list[0]}
        
        elif all([val == False for val in truth_dict.values()]):
            # If no points in the same Continents, Country, Region, and County
            tmp_config['sentence'] = '{ttl_0} of interest'
            tmp_config['items'] = {'ttl_0': land_sea_phrase}
        
        elif all([val == True for key, val in truth_dict.items() if key in ['continent', 'country', 'region'] ]):
            # If Continents, Country, Region in the same place, but not County
            tmp_config['sentence'] = '{ttl_0} in {ttl_1}, {ttl_2}'
            tmp_config['items'] = {'ttl_0': land_sea_phrase, 'ttl_1': region_list[0], 'ttl_2': country_list[0]}
        
        elif all([val == True for key, val in truth_dict.items() if key in ['continent', 'country']]):
            # If Continents, Country in the same place, but not Region or County
            if len(set(region_list)) == 2:
                tmp_config['sentence'] = '{ttl_0} between {ttl_1} and {ttl_2}, {ttl_3}'
                tmp_config['items'] = {'ttl_0': land_sea_phrase, 'ttl_1': list(set(region_list))[0], 'ttl_2': list(set(region_list))[1], 'ttl_3': country_list[0]}
            elif len(set(region_list)) > 2:
                # If location across multiple regions (get the centroid's region)
                tmp_config['sentence'] = '{ttl_0} near {ttl_1}, {ttl_2}'
                tmp_config['items'] = {'ttl_0': land_sea_phrase, 'ttl_1': region_list[-1], 'ttl_2': country_list[0]}
    
        else:
            # If only Continents
            if len(set(country_list)) == 2:
                # If location across two countries
                tmp_config['sentence'] = '{ttl_0} between {ttl_1} and {ttl_2}, in {ttl_3}'
                tmp_config['items'] = {'ttl_0': land_sea_phrase, 'ttl_1': list(set(country_list))[0], 'ttl_2': list(set(country_list))[1], 'ttl_3': continent_list[0]}
            elif len(set(country_list)) > 2:
                # If location across multiple countries (get the centroid's country)   
                tmp_config['sentence'] = '{ttl_0} near {ttl_1}, {ttl_2}'
                tmp_config['items'] = {'ttl_0': land_sea_phrase, 'ttl_1': country_list[-1], 'ttl_3': continent_list[0]}
        
        return tmp_config
        
    @staticmethod
    def give_sorted_d(lookup_dic, key, stats):
        """Return a dic with keys as integer percentage of coverage proportion."""
        total = 0
        for item in stats.get(key):
            total += stats.get(key).get(item)
        tmp_d = {}
        for item in stats.get(key):
            tmp_proportion = int((stats.get(key).get(item)/ total) * 100)
            tmp_d[tmp_proportion] = lookup_dic[item]
        s_dic = {}
        for kk in sorted(tmp_d,reverse=True):
            s_dic[kk] = tmp_d[kk]
        return s_dic

    @staticmethod
    def gen_ecoregion_sentence(stats):
        ecoregion_sentence = None
        tmp_d = GeodescriberService.give_sorted_d(ecoid_to_ecoregion, 'ecoregion', stats)
        proportion_list = list(tmp_d.keys())
        tmp_config = {'items': {}, 'sentence': ""}
        if not proportion_list:
            return None
        elif proportion_list[0] > 75:
            tmp_config['sentence'] = "The regions habitat is comprised of {eco_0}."
            tmp_config['items'] = {'eco_0': tmp_d[proportion_list[0]]}
        elif proportion_list[0] > 50:
            tmp_config['sentence'] = "The majority of the regions habitat is comprised of {eco_0}. It also includes areas of {eco_1}."
            tmp_config['items'] = {'eco_0': tmp_d[proportion_list[0]], 'eco_1': tmp_d[proportion_list[1]]}
        else:
            tmp_config['sentence'] = "The region is made up of different habitats, including {eco_0}, and {eco_1}."
            tmp_config['items'] = {'eco_0': tmp_d[proportion_list[0]], 'eco_1': tmp_d[proportion_list[1]]}
        return tmp_config

    @staticmethod
    def gen_land_sea_title(stats):
        land = stats.get('seaLandFreshwater').get('0', 0)
        sea = stats.get('seaLandFreshwater').get('1', 0)
        fresh = stats.get('seaLandFreshwater').get('2', 0)
        water = sea + fresh

        total_land_sea = land + sea + fresh
        land_sea_sentence = ''

        if sea/total_land_sea > 0.66:
            land_sea_sentence = "Marine"
        elif fresh/total_land_sea > 0.66:
            land_sea_sentence = "Inland water"
        return land_sea_sentence

    @staticmethod
    def gen_land_sea_sentence(stats):
        tmp_config = {'items': {}, 'sentence': ""}

        land = stats.get('seaLandFreshwater').get('0', 0)
        sea = stats.get('seaLandFreshwater').get('1', 0)
        fresh = stats.get('seaLandFreshwater').get('2', 0)
        total_land_sea = land + sea + fresh
        land_sea_list = sorted([l for l in [
            {"type": 'land area', "value": land/total_land_sea},
            {"type": 'marine areas', "value": sea/total_land_sea},
            {"type": 'inland water', "value": fresh/total_land_sea}]
            if l['value']], key=lambda k: k['value'], reverse=True) 
        
        logging.info(f'[Geodescriber]: land_sea: {land_sea_list}')
        
        land_sea_sentence = ''
        
        if land_sea_list[0]['value'] > 0.9:
            tmp_config['sentence'] = "The location is predominantly {lsf_0}."
            tmp_config['items'] = {'lsf_0': land_sea_list[0]['type']}
        elif len(land_sea_list) == 2:
            if land_sea_list[0]['value'] > 0.75:
                tmp_config['sentence'] = "The location is mostly {lsf_0} with some {lsf_1}."
                tmp_config['items'] = {'lsf_0': land_sea_list[0]['type'], 'lsf_1': land_sea_list[1]['type']}
            else:
                tmp_config['sentence'] = "The location is mostly {lsf_0} with a large proportion of {lsf_1}."
                tmp_config['items'] = {'lsf_0': land_sea_list[0]['type'], 'lsf_1': land_sea_list[1]['type']}
        elif land_sea_list[0]['value'] > 0.5:
            if land_sea_list[1]['value'] > (1 - land_sea_list[0]['value']) * 0.75:
                tmp_config['sentence'] = "The location is mostly {lsf_0} with some {lsf_1}."
                tmp_config['items'] = {'lsf_0': land_sea_list[0]['type'], 'lsf_1': land_sea_list[1]['type']}
            else:
                tmp_config['sentence'] = "The location is mostly {lsf_0} with a mix of {lsf_1} and {lsf_2}."
                tmp_config['items'] = {'lsf_0': land_sea_list[0]['type'], 'lsf_1': land_sea_list[1]['type'], 'lsf_2': land_sea_list[2]['type']}
        elif land_sea_list[0]['value'] + land_sea_list[1]['value'] > 0.5:
                tmp_config['sentence'] = "The location is mostly a mix of {lsf_0} and {lsf_1}."
                tmp_config['items'] = {'lsf_0': land_sea_list[0]['type'], 'lsf_1': land_sea_list[1]['type']}
        else:
            tmp_config['sentence'] = "The location contains a mix of {lsf_0}, {lsf_1} and {lsf_2}."
            tmp_config['items'] = {'lsf_0': land_sea_list[0]['type'], 'lsf_1': land_sea_list[1]['type'], 'lsf_2': land_sea_list[2]['type']}
        
        return tmp_config

    @staticmethod
    def gen_intact_sentence(stats):
        not_intact = stats.get('intact2016').get('0', 0)
        is_intact = stats.get('intact2016').get('1', 0)
        total_intact = not_intact + is_intact
        intact_sentence = None
        tmp_config = {'items': {}, 'sentence': ""}
        if is_intact:
            if is_intact/total_intact > 0.75:
                tmp_config['sentence'] = "This region contains a large amount of Intact Forest."
            elif is_intact/total_intact > 0.5:
                tmp_config['sentence'] = "This region contains Intact Forest."
            else:
                tmp_config['sentence'] = "This region contains some Intact Forest."
        else:
            tmp_config['sentence'] = 'This region has no Intact Forest.'
        return tmp_config

    @staticmethod
    def gen_mountain_sentence(stats):
        is_mountain = stats.get('isMountain').get('1', 0)
        not_mountain = stats.get('isMountain').get('0', 0)
        total_mountain = not_mountain + is_mountain
        mountain_sentence = None
        tmp_config = {'items': {}, 'sentence': ""}
        if is_mountain:
            if is_mountain/total_mountain > 0.75:
                tmp_config['sentence'] = "a mountainous area"
            elif is_mountain/total_mountain > 0.5:
                tmp_config['sentence'] = "a mix of lowland and mountains areas"
            else:
                tmp_config['sentence'] = "a predominanty lowland area"
        else:
            tmp_config['sentence'] = "a lowland area"
        return tmp_config

    @staticmethod
    def gen_koppen_sentence(stats):
        # create a sorted list of items to deal with possilities of different Koppen climates
        tmp_d = GeodescriberService.give_sorted_d(lookup_dic=koppen_translated, key='koppen',stats=stats)
        proportion_list = list(tmp_d.keys())
        tmp_config = {'items': {}, 'sentence': ""}
        if not proportion_list:
            return None
        elif proportion_list[0] > 75:
            tmp_config['sentence'] = "The area has a predominantly {kop_0}."
            tmp_config['items'] = {'kop_0': tmp_d[proportion_list[0]]}
        elif proportion_list[0] > 50:
            tmp_config['sentence'] = "The majority of the region has {kop_0}. It also has areas of {kop_1}."
            tmp_config['items'] = {'kop_0': tmp_d[proportion_list[0]], 'kop_1': tmp_d[proportion_list[1]]}
        else:
            tmp_config['sentence'] = "The most common environmental conditions of the area are {kop_0}."
            tmp_config['items'] = {'kop_0': tmp_d[proportion_list[0]]}
        return tmp_config

    @staticmethod
    def gen_biome_sentence(stats):
        biome_sentence = None
        tmp_d = GeodescriberService.give_sorted_d(biomeNum_2_biomeName, 'biome', stats)
        proportion_list = list(tmp_d.keys())
        tmp_config = {'items': {}, 'sentence': ""}
        if not proportion_list:
            return None
        elif proportion_list[0] > 75:
            tmp_config['sentence'] = "It is part of the {bio_0} biome."
            tmp_config['items'] = {'bio_0': tmp_d[proportion_list[0]]}
        elif proportion_list[0] > 50:
            tmp_config['sentence'] = "The majority of the region is comprised of {bio_0}. It also includes areas of {bio_1}."
            tmp_config['items'] = {'bio_0': tmp_d[proportion_list[0]], 'bio_1': tmp_d[proportion_list[1]]}
        else:
            tmp_config['sentence'] = "The region is made up of several types of biomes, including {bio_0}, and {bio_1}."
            tmp_config['items'] = {'bio_0': tmp_d[proportion_list[0]], 'bio_1': tmp_d[proportion_list[1]]}

        return tmp_config

    @staticmethod
    def gen_area_sentence(area_ha, app, mountain_sentence, title_elements):
        tmp_config = {'items': {}, 'sentence': ""}
        if title_elements:
            try:
                title_ele = ' in ' + title_elements[0]
            except:
                title_ele = ''
        else:
            return None
        if app == 'gfw':
            tmp_config['sentence'] = "Area of {area_0} located in {area_1}{area_2}."
            tmp_config['items'] = {'area_0': f'{human_format(area_ha)}ha', 'area_1': mountain_sentence, 'area_2': title_ele}
        else:
            tmp_config['sentence'] = "Area of {area_0} located in {area_1}{area_2}."
            tmp_config['items'] = {'area_0': f'{area_ha * 0.01:3,.0f}km²', 'area_1': mountain_sentence, 'area_2': title_ele}
        return tmp_config

    @staticmethod
    def analyze(geojson, area_ha=None, lang='en', app='gfw', template=False):
        """Recieve a geostore_id, language, and app argument and return a
        json serialised dic object response.
        """
        
        logging.info(f'[Geodescriber]: app={app}, lang={lang}, template={template}, for geojson={geojson}')
        sentence_config = []
        features = geojson.get('features')
        s = [shape(feature['geometry']) for feature in features][0]
        logging.info(f'[Geodescriber]: shape: {s}')
        #g = LMIPy.Geometry(geostore_id)

        asset_name = SETTINGS.get('gee').get('assets').get('geodescriber')
        logging.info(f'[Geodescriber]: asset: {asset_name}')
        img = ee.Image(asset_name) # Grab the layer
        region = get_region(geojson) # Create an EE feature from a geostore object
        try:
            stats = img.reduceRegion(**{'reducer': ee.Reducer.frequencyHistogram(),
                                        'geometry': region,
                                        'bestEffort': True,
                                        }).getInfo()
            logging.info(f'[Geodescriber]: stats: {stats}')    
        except:
            logging.error('[Geodescriber]: EE failed.')
            stats = {}

        land_sea_sentence = GeodescriberService.gen_land_sea_title(stats)
        title_elements = GeodescriberService.create_title_elements(s)
        title = GeodescriberService.create_title(title_elements, land_sea_sentence)
        logging.info(f'[Geodescriber]: title: {title}')

        if any([v != {} for k,v in stats.items() if k != 'intact2016']): 

            ecoregion_sentence = GeodescriberService.gen_ecoregion_sentence(stats)
            if ecoregion_sentence: sentence_config.append(ecoregion_sentence)
            # logging.info(f'[Geodescriber]: ecoregion: {ecoregion_sentence}')

            intact_sentence = GeodescriberService.gen_intact_sentence(stats)
            if intact_sentence: sentence_config.append(intact_sentence)
            # logging.info(f'[Geodescriber]: intact: {intact_sentence}')

            mountain_sentence = GeodescriberService.gen_mountain_sentence(stats)
            # if mountain_sentence: sentence_config.append(mountain_sentence)
            # logging.info(f'[Geodescriber]: mountain: {mountain_sentence}')

            koppen_sentence = GeodescriberService.gen_koppen_sentence(stats)
            if koppen_sentence: sentence_config.append(koppen_sentence)
            # logging.info(f'[Geodescriber]: koppen: {koppen_sentence}')

            biome_sentence = GeodescriberService.gen_biome_sentence(stats)
            if biome_sentence: sentence_config.append(biome_sentence)
            # logging.info(f'[Geodescriber]: biome: {biome_sentence}')

            land_sea_sentence = GeodescriberService.gen_land_sea_sentence(stats)
            if land_sea_sentence: sentence_config.append(land_sea_sentence)
            # logging.info(f'[Geodescriber]: biome: {biome_sentence}')

            area_sentence = GeodescriberService.gen_area_sentence(area_ha=area_ha, app=app, mountain_sentence=mountain_sentence['sentence'], title_elements=title_elements)
            if area_sentence: sentence_config.append(area_sentence)
            # logging.info(f'[Geodescriber]: area: {area_sentence}')

        ### BUILD SENTENCE HERE IF TEMPLATE=FALSE
        description = ""
        description_params = {}
        title_params = title['items']
        title = title['sentence']

        for el in sentence_config:
            description += f"{el.get('sentence', '')} "
            description_params = {**description_params, **el.get('items')}
            if lang != 'en':
                translator = Translator()
                r = translator.translate(text=[title, description], dest=lang, src='en')
                title = r[0].text
                description = r[1].text

                rt = translator.translate(text=[v for k,v in title_params.items()], dest=lang, src='en')
                rd = translator.translate(text=[v for k,v in description_params.items()], dest=lang, src='en')

                title_params = {k:rt[i].text for i,k in enumerate(title_params.keys())}
                description_params = {k:rd[i].text for i,k in enumerate(description_params.keys())}
                
        if not template:
            for k,v in title_params.items():
                title = title.replace(f'{{{k}}}', v)
            for k,v in description_params.items():
                description = description.replace(f'{{{k}}}', v) 
        
            if lang is not 'en':
                translator = Translator()
                r = translator.translate(text=[title, description], dest=lang, src='en')
                title = r[0].text
                description = r[1].text
            logging.info(f'[Geodescriber]: description: {description}')

            return {
            'title': title,
            'title_params': {},
            'description':description[:-1], 
            'description_params': {}, 
            'lang': lang,
            'stats': stats
            }

        return {
            'title': title,
            'title_params': title_params,
            'description':description[:-1], 
            'description_params': description_params, 
            'lang': lang,
            'stats': stats
            }

continent_lookup = {
    None: None,
    'AF':'Africa',
    'AN':'Antarctica',
    'AS':'Asia',
    'EU':'Europe',
    'NA':'North america',
    'OC':'Oceania',
    'SA':'South america'
    }

iso_to_continent = {
'': None,
'AD':'EU',
'AE':'AS',
'AF':'AS',
'AG':'NA',
'AI':'NA',
'AL':'EU',
'AM':'AS',
'AO':'AF',
'AP':'AS',
'AN':'NA',
'AQ':'AN',
'AR':'SA',
'AS':'OC',
'AT':'EU',
'AU':'OC',
'AW':'NA',
'AX':'EU',
'AZ':'AS',
'BA':'EU',
'BB':'NA',
'BD':'AS',
'BE':'EU',
'BF':'AF',
'BG':'EU',
'BH':'AS',
'BI':'AF',
'BJ':'AF',
'BL':'NA',
'BM':'NA',
'BN':'AS',
'BO':'SA',
'BR':'SA',
'BS':'NA',
'BT':'AS',
'BV':'AN',
'BW':'AF',
'BY':'EU',
'BZ':'NA',
'CA':'NA',
'CC':'AS',
'CD':'AF',
'CF':'AF',
'CG':'AF',
'CH':'EU',
'CI':'AF',
'CK':'OC',
'CL':'SA',
'CM':'AF',
'CN':'AS',
'CO':'SA',
'CR':'NA',
'CU':'NA',
'CV':'AF',
'CX':'AS',
'CY':'AS',
'CZ':'EU',
'DE':'EU',
'DJ':'AF',
'DK':'EU',
'DM':'NA',
'DO':'NA',
'DZ':'AF',
'EC':'SA',
'EE':'EU',
'EG':'AF',
'EH':'AF',
'ER':'AF',
'ES':'EU',
'ET':'AF',
'EU':'EU',
'FI':'EU',
'FJ':'OC',
'FK':'SA',
'FM':'OC',
'FO':'EU',
'FR':'EU',
'FX':'EU',
'GA':'AF',
'GB':'EU',
'GD':'NA',
'GE':'AS',
'GF':'SA',
'GG':'EU',
'GH':'AF',
'GI':'EU',
'GL':'NA',
'GM':'AF',
'GN':'AF',
'GP':'NA',
'GQ':'AF',
'GR':'EU',
'GS':'AN',
'GT':'NA',
'GU':'OC',
'GW':'AF',
'GY':'SA',
'HK':'AS',
'HM':'AN',
'HN':'NA',
'HR':'EU',
'HT':'NA',
'HU':'EU',
'ID':'AS',
'IE':'EU',
'IL':'AS',
'IM':'EU',
'IN':'AS',
'IO':'AS',
'IQ':'AS',
'IR':'AS',
'IS':'EU',
'IT':'EU',
'JE':'EU',
'JM':'NA',
'JO':'AS',
'JP':'AS',
'KE':'AF',
'KG':'AS',
'KH':'AS',
'KI':'OC',
'KM':'AF',
'KN':'NA',
'KP':'AS',
'KR':'AS',
'KW':'AS',
'KY':'NA',
'KZ':'AS',
'LA':'AS',
'LB':'AS',
'LC':'NA',
'LI':'EU',
'LK':'AS',
'LR':'AF',
'LS':'AF',
'LT':'EU',
'LU':'EU',
'LV':'EU',
'LY':'AF',
'MA':'AF',
'MC':'EU',
'MD':'EU',
'ME':'EU',
'MF':'NA',
'MG':'AF',
'MH':'OC',
'MK':'EU',
'ML':'AF',
'MM':'AS',
'MN':'AS',
'MO':'AS',
'MP':'OC',
'MQ':'NA',
'MR':'AF',
'MS':'NA',
'MT':'EU',
'MU':'AF',
'MV':'AS',
'MW':'AF',
'MX':'NA',
'MY':'AS',
'MZ':'AF',
'NA':'AF',
'NC':'OC',
'NE':'AF',
'NF':'OC',
'NG':'AF',
'NI':'NA',
'NL':'EU',
'NO':'EU',
'NP':'AS',
'NR':'OC',
'NU':'OC',
'NZ':'OC',
'O1':'--',
'OM':'AS',
'PA':'NA',
'PE':'SA',
'PF':'OC',
'PG':'OC',
'PH':'AS',
'PK':'AS',
'PL':'EU',
'PM':'NA',
'PN':'OC',
'PR':'NA',
'PS':'AS',
'PT':'EU',
'PW':'OC',
'PY':'SA',
'QA':'AS',
'RE':'AF',
'RO':'EU',
'RS':'EU',
'RU':'EU',
'RW':'AF',
'SA':'AS',
'SB':'OC',
'SC':'AF',
'SD':'AF',
'SE':'EU',
'SG':'AS',
'SH':'AF',
'SI':'EU',
'SJ':'EU',
'SK':'EU',
'SL':'AF',
'SM':'EU',
'SN':'AF',
'SO':'AF',
'SR':'SA',
'ST':'AF',
'SV':'NA',
'SY':'AS',
'SZ':'AF',
'TC':'NA',
'TD':'AF',
'TF':'AN',
'TG':'AF',
'TH':'AS',
'TJ':'AS',
'TK':'OC',
'TL':'AS',
'TM':'AS',
'TN':'AF',
'TO':'OC',
'TR':'EU',
'TT':'NA',
'TV':'OC',
'TW':'AS',
'TZ':'AF',
'UA':'EU',
'UG':'AF',
'UM':'OC',
'US':'NA',
'UY':'SA',
'UZ':'AS',
'VA':'EU',
'VC':'NA',
'VE':'SA',
'VG':'NA',
'VI':'NA',
'VN':'AS',
'VU':'OC',
'WF':'OC',
'WS':'OC',
'YE':'AS',
'YT':'AF',
'ZA':'AF',
'ZM':'AF',
'ZW':'AF'}

koppen = {
    '11': 'Af',
    '12': 'Am',
    '13': 'As',
    '14': 'Aw',
    '21': 'BWk',
    '22': 'BWh',
    '26': 'BSk',
    '27': 'BSh',
    '31': 'Cfa',
    '32': 'Cfb',
    '33': 'Cfc',
    '34': 'Csa',
    '35': 'Csb',
    '36': 'Csc',
    '37': 'Cwa',
    '38': 'Cwb',
    '39': 'Cwc',
    '41': 'Dfa',
    '42': 'Dfb',
    '43': 'Dfc',
    '44': 'Dfd',
    '45': 'Dsa',
    '46': 'Dsb',
    '47': 'Dsc',
    '48': 'Dsd',
    '49': 'Dwa',
    '50': 'Dwb',
    '51': 'Dwc',
    '52': 'Dwd',
    '61': 'EF',
    '62': 'ET'
    }

koppen_translated = {
    '11': 'equatorial, humid climate',
    '12': 'equatorial, with monsoonal rainfall',
    '13': 'equatorial climate with dry summers',
    '14': 'equatorial climate with dry winters',
    '21': 'arid desert climate with cold temperatures',
    '22': 'arid desert climate with hot temperatures',
    '26': 'semi-arid climate with cold temperatures',
    '27': 'semi-arid climate with hot temperatures',
    '31': 'warm and temperate climate with high humidity and hot summers',
    '32': 'warm and temperate climate with high humidity and warm summers',
    '33': 'warm and temperate climate with high humidity and cool summers',
    '34': 'warm and temperate climate with dry, hot summers',
    '35': 'warm and temperate climate with dry summers',
    '36': 'warm and temperate climate with dry, cool summers',
    '37': 'warm and temperate climate with dry winters and hot summers',
    '38': 'warm and temperate climate with dry winters and warm summers',
    '39': 'warm and temperate climate with dry winters and cool summers',
    '41': 'snowy, humid climate with hot summers',
    '42': 'snowy, humid climate with warm summers',
    '43': 'snowy, humid climate with cool summers',
    '44': 'snowy, humid, and continental climate',
    '45': 'snowy climate with dry, hot summers',
    '46': 'snowy climate with dry warm summers',
    '47': 'snowy climate with dry cool summers',
    '48': 'snowy climate with dry summers and extremly continental temperatures',
    '49': 'snowy climate with dry winters and hot summers',
    '50': 'snowy climate with dry winters and warm summers',
    '51': 'snowy climate with dry winters and cool summers',
    '52': 'snowy climate with dry winters and extremley continental temperatures',
    '61': 'polar, perpetual frost climate',
    '62': 'polar tundra climate'
    }

ecoid_to_ecoregion = {'0': 'rock and ice',
 '1': 'Albertine Rift montane forests',
 '2': 'Cameroon Highlands forests',
 '3': 'Central Congolian lowland forests',
 '4': 'Comoros forests',
 '5': 'Congolian coastal forests',
 '6': 'Cross-Niger transition forests',
 '7': 'Cross-Sanaga-Bioko coastal forests',
 '8': 'East African montane forests',
 '9': 'Eastern Arc forests',
 '10': 'Eastern Congolian swamp forests',
 '11': 'Eastern Guinean forests',
 '12': 'Ethiopian montane forests',
 '13': 'Granitic Seychelles forests',
 '14': 'Guinean montane forests',
 '15': 'Knysna-Amatole montane forests',
 '16': 'Kwazulu Natal-Cape coastal forests',
 '17': 'Madagascar humid forests',
 '18': 'Madagascar subhumid forests',
 '19': 'Maputaland coastal forests and woodlands',
 '20': 'Mascarene forests',
 '21': 'Mount Cameroon and Bioko montane forests',
 '22': 'Niger Delta swamp forests',
 '23': 'Nigerian lowland forests',
 '24': 'Northeast Congolian lowland forests',
 '25': 'Northern Swahili coastal forests',
 '26': 'Northwest Congolian lowland forests',
 '27': 'São Tomé, Príncipe, and Annobón forests',
 '28': 'Southern Swahili coastal forests and woodlands',
 '29': 'Western Congolian swamp forests',
 '30': 'Western Guinean lowland forests',
 '31': 'Cape Verde Islands dry forests',
 '32': 'Madagascar dry deciduous forests',
 '33': 'Zambezian evergreen dry forests',
 '34': 'Angolan mopane woodlands',
 '35': 'Angolan scarp savanna and woodlands',
 '36': 'Angolan wet miombo woodlands',
 '37': 'Ascension scrub and grasslands',
 '38': 'Central bushveld',
 '39': 'Central Zambezian wet miombo woodlands',
 '40': 'Drakensberg Escarpment savanna and thicket',
 '41': 'Drakensberg grasslands',
 '42': 'Dry miombo woodlands',
 '43': 'East Sudanian savanna',
 '44': 'Guinean forest-savanna',
 '45': 'Horn of Africa xeric bushlands',
 '46': 'Itigi-Sumbu thicket',
 '47': 'Kalahari Acacia woodlands',
 '48': 'Limpopo lowveld',
 '49': 'Mandara Plateau woodlands',
 '50': 'Masai xeric grasslands and shrublands',
 '51': 'Northern Acacia-Commiphora bushlands and thickets',
 '52': 'Northern Congolian Forest-Savanna',
 '53': 'Sahelian Acacia savanna',
 '54': 'Serengeti volcanic grasslands',
 '55': 'Somali Acacia-Commiphora bushlands and thickets',
 '56': 'South Arabian fog woodlands, shrublands, and dune',
 '57': 'Southern Acacia-Commiphora bushlands and thickets',
 '58': 'Southern Congolian forest-savanna',
 '59': 'Southwest Arabian montane woodlands and grasslands',
 '60': 'St. Helena scrub and woodlands',
 '61': 'Victoria Basin forest-savanna',
 '62': 'West Sudanian savanna',
 '63': 'Western Congolian forest-savanna',
 '64': 'Zambezian Baikiaea woodlands',
 '65': 'Zambezian mopane woodlands',
 '66': 'Zambezian-Limpopo mixed woodlands',
 '67': 'Amsterdam-Saint Paul Islands temperate grasslands',
 '68': 'Tristan Da Cunha-Gough Islands shrub and grasslands',
 '69': 'East African halophytics',
 '70': 'Etosha Pan halophytics',
 '71': 'Inner Niger Delta flooded savanna',
 '72': 'Lake Chad flooded savanna',
 '73': 'Makgadikgadi halophytics',
 '74': 'Sudd flooded grasslands',
 '75': 'Zambezian coastal flooded savanna',
 '76': 'Zambezian flooded grasslands',
 '77': 'Angolan montane forest-grassland',
 '78': 'East African montane moorlands',
 '79': 'Ethiopian montane grasslands and woodlands',
 '80': 'Ethiopian montane moorlands',
 '81': 'Highveld grasslands',
 '82': 'Jos Plateau forest-grassland',
 '83': 'Madagascar ericoid thickets',
 '84': 'Mulanje Montane forest-grassland',
 '85': 'Nyanga-Chimanimani Montane forest-grassland',
 '86': 'Rwenzori-Virunga montane moorlands',
 '87': 'Southern Rift Montane forest-grassland',
 '88': 'Albany thickets',
 '89': 'Fynbos shrubland',
 '90': 'Renosterveld shrubland',
 '91': 'Aldabra Island xeric scrub',
 '92': 'Djibouti xeric shrublands',
 '93': 'Eritrean coastal desert',
 '94': 'Gariep Karoo',
 '95': 'Hobyo grasslands and shrublands',
 '96': 'Ile Europa and Bassas da India xeric scrub',
 '97': 'Kalahari xeric savanna',
 '98': 'Kaokoveld desert',
 '99': 'Madagascar spiny thickets',
 '100': 'Madagascar succulent woodlands',
 '101': 'Nama Karoo shrublands',
 '102': 'Namaqualand-Richtersveld steppe',
 '103': 'Namib Desert',
 '104': 'Namibian savanna woodlands',
 '105': 'Socotra Island xeric shrublands',
 '106': 'Somali montane xeric woodlands',
 '107': 'Southwest Arabian coastal xeric shrublands',
 '108': 'Southwest Arabian Escarpment shrublands and woodlands',
 '109': 'Southwest Arabian highland xeric scrub',
 '110': 'Succulent Karoo xeric shrublands',
 '111': 'Central African mangroves',
 '112': 'East African mangroves',
 '113': 'Guinean mangroves',
 '114': 'Madagascar mangroves',
 '115': 'Red Sea mangroves',
 '116': 'Southern Africa mangroves',
 '117': 'Adelie Land tundra',
 '118': 'Central South Antarctic Peninsula tundra',
 '119': 'Dronning Maud Land tundra',
 '120': 'East Antarctic tundra',
 '121': 'Ellsworth Land tundra',
 '122': 'Ellsworth Mountains tundra',
 '123': 'Enderby Land tundra',
 '124': 'Marie Byrd Land tundra',
 '125': 'North Victoria Land tundra',
 '126': 'Northeast Antarctic Peninsula tundra',
 '127': 'Northwest Antarctic Peninsula tundra',
 '128': 'Prince Charles Mountains tundra',
 '129': 'Scotia Sea Islands tundra',
 '130': 'South Antarctic Peninsula tundra',
 '131': 'South Orkney Islands tundra',
 '132': 'South Victoria Land tundra',
 '133': 'Southern Indian Ocean Islands tundra',
 '134': 'Transantarctic Mountains tundra',
 '135': 'Admiralty Islands lowland rain forests',
 '136': 'Banda Sea Islands moist deciduous forests',
 '137': 'Biak-Numfoor rain forests',
 '138': 'Buru rain forests',
 '139': 'Central Range Papuan montane rain forests',
 '140': 'Halmahera rain forests',
 '141': 'Huon Peninsula montane rain forests',
 '142': 'Lord Howe Island subtropical forests',
 '143': 'Louisiade Archipelago rain forests',
 '144': 'New Britain-New Ireland lowland rain forests',
 '145': 'New Britain-New Ireland montane rain forests',
 '146': 'New Caledonia rain forests',
 '147': 'Norfolk Island subtropical forests',
 '148': 'Northern New Guinea lowland rain and freshwater swamp forests',
 '149': 'Northern New Guinea montane rain forests',
 '150': 'Queensland tropical rain forests',
 '151': 'Seram rain forests',
 '152': 'Solomon Islands rain forests',
 '153': 'Southeast Papuan rain forests',
 '154': 'Southern New Guinea freshwater swamp forests',
 '155': 'Southern New Guinea lowland rain forests',
 '156': 'Sulawesi lowland rain forests',
 '157': 'Sulawesi montane rain forests',
 '158': 'Trobriand Islands rain forests',
 '159': 'Vanuatu rain forests',
 '160': 'Vogelkop montane rain forests',
 '161': 'Vogelkop-Aru lowland rain forests',
 '162': 'Yapen rain forests',
 '163': 'Lesser Sundas deciduous forests',
 '164': 'New Caledonia dry forests',
 '165': 'Sumba deciduous forests',
 '166': 'Timor and Wetar deciduous forests',
 '167': 'Chatham Island temperate forests',
 '168': 'Eastern Australian temperate forests',
 '169': 'Fiordland temperate forests',
 '170': 'Nelson Coast temperate forests',
 '171': 'New Zealand North Island temperate forests',
 '172': 'New Zealand South Island temperate forests',
 '173': 'Northland temperate kauri forests',
 '174': 'Rakiura Island temperate forests',
 '175': 'Richmond temperate forests',
 '176': 'Southeast Australia temperate forests',
 '177': 'Tasmanian Central Highland forests',
 '178': 'Tasmanian temperate forests',
 '179': 'Tasmanian temperate rain forests',
 '180': 'Westland temperate forests',
 '181': 'Arnhem Land tropical savanna',
 '182': 'Brigalow tropical savanna',
 '183': 'Cape York Peninsula tropical savanna',
 '184': 'Carpentaria tropical savanna',
 '185': 'Einasleigh upland savanna',
 '186': 'Kimberly tropical savanna',
 '187': 'Mitchell Grass Downs',
 '188': 'Trans Fly savanna and grasslands',
 '189': 'Victoria Plains tropical savanna',
 '190': 'Canterbury-Otago tussock grasslands',
 '191': 'Eastern Australia mulga shrublands',
 '192': 'Southeast Australia temperate savanna',
 '193': 'Australian Alps montane grasslands',
 '194': 'New Zealand South Island montane grasslands',
 '195': 'Papuan Central Range sub-alpine grasslands',
 '196': 'Antipodes Subantarctic Islands tundra',
 '197': 'Coolgardie woodlands',
 '198': 'Esperance mallee',
 '199': 'Eyre and York mallee',
 '200': 'Flinders-Lofty montane woodlands',
 '201': 'Hampton mallee and woodlands',
 '202': 'Jarrah-Karri forest and shrublands',
 '203': 'Murray-Darling woodlands and mallee',
 '204': 'Naracoorte woodlands',
 '205': 'Southwest Australia savanna',
 '206': 'Southwest Australia woodlands',
 '207': 'Carnarvon xeric shrublands',
 '208': 'Central Ranges xeric scrub',
 '209': 'Gibson desert',
 '210': 'Great Sandy-Tanami desert',
 '211': 'Great Victoria desert',
 '212': 'Nullarbor Plains xeric shrublands',
 '213': 'Pilbara shrublands',
 '214': 'Simpson desert',
 '215': 'Tirari-Sturt stony desert',
 '216': 'Western Australian Mulga shrublands',
 '217': 'New Guinea mangroves',
 '218': 'Andaman Islands rain forests',
 '219': 'Borneo lowland rain forests',
 '220': 'Borneo montane rain forests',
 '221': 'Borneo peat swamp forests',
 '222': 'Brahmaputra Valley semi-evergreen forests',
 '223': 'Cardamom Mountains rain forests',
 '224': 'Chao Phraya freshwater swamp forests',
 '225': 'Chao Phraya lowland moist deciduous forests',
 '226': 'Chin Hills-Arakan Yoma montane forests',
 '227': 'Christmas and Cocos Islands tropical forests',
 '228': 'East Deccan moist deciduous forests',
 '229': 'Eastern Java-Bali montane rain forests',
 '230': 'Eastern Java-Bali rain forests',
 '231': 'Greater Negros-Panay rain forests',
 '232': 'Hainan Island monsoon rain forests',
 '233': 'Himalayan subtropical broadleaf forests',
 '234': 'Irrawaddy freshwater swamp forests',
 '235': 'Irrawaddy moist deciduous forests',
 '236': 'Jian Nan subtropical evergreen forests',
 '237': 'Kayah-Karen montane rain forests',
 '238': 'Lower Gangetic Plains moist deciduous forests',
 '239': 'Luang Prabang montane rain forests',
 '240': 'Luzon montane rain forests',
 '241': 'Luzon rain forests',
 '242': 'Malabar Coast moist forests',
 '243': 'Maldives-Lakshadweep-Chagos Archipelago tropical moist forests',
 '244': 'Meghalaya subtropical forests',
 '245': 'Mentawai Islands rain forests',
 '246': 'Mindanao montane rain forests',
 '247': 'Mindanao-Eastern Visayas rain forests',
 '248': 'Mindoro rain forests',
 '249': 'Mizoram-Manipur-Kachin rain forests',
 '250': 'Myanmar coastal rain forests',
 '251': 'Nansei Islands subtropical evergreen forests',
 '252': 'Nicobar Islands rain forests',
 '253': 'North Western Ghats moist deciduous forests',
 '254': 'North Western Ghats montane rain forests',
 '255': 'Northern Annamites rain forests',
 '256': 'Northern Indochina subtropical forests',
 '257': 'Northern Khorat Plateau moist deciduous forests',
 '258': 'Northern Thailand-Laos moist deciduous forests',
 '259': 'Northern Triangle subtropical forests',
 '260': 'Northern Vietnam lowland rain forests',
 '261': 'Orissa semi-evergreen forests',
 '262': 'Palawan rain forests',
 '263': 'Peninsular Malaysian montane rain forests',
 '264': 'Peninsular Malaysian peat swamp forests',
 '265': 'Peninsular Malaysian rain forests',
 '266': 'Red River freshwater swamp forests',
 '267': 'South China Sea Islands',
 '268': 'South China-Vietnam subtropical evergreen forests',
 '269': 'South Taiwan monsoon rain forests',
 '270': 'South Western Ghats moist deciduous forests',
 '271': 'South Western Ghats montane rain forests',
 '272': 'Southern Annamites montane rain forests',
 '273': 'Southwest Borneo freshwater swamp forests',
 '274': 'Sri Lanka lowland rain forests',
 '275': 'Sri Lanka montane rain forests',
 '276': 'Sulu Archipelago rain forests',
 '277': 'Sumatran freshwater swamp forests',
 '278': 'Sumatran lowland rain forests',
 '279': 'Sumatran montane rain forests',
 '280': 'Sumatran peat swamp forests',
 '281': 'Sundaland heath forests',
 '282': 'Sundarbans freshwater swamp forests',
 '283': 'Taiwan subtropical evergreen forests',
 '284': 'Tenasserim-South Thailand semi-evergreen rain forests',
 '285': 'Tonle Sap freshwater swamp forests',
 '286': 'Tonle Sap-Mekong peat swamp forests',
 '287': 'Upper Gangetic Plains moist deciduous forests',
 '288': 'Western Java montane rain forests',
 '289': 'Western Java rain forests',
 '290': 'Central Deccan Plateau dry deciduous forests',
 '291': 'Central Indochina dry forests',
 '292': 'Chhota-Nagpur dry deciduous forests',
 '293': 'East Deccan dry-evergreen forests',
 '294': 'Irrawaddy dry forests',
 '295': 'Khathiar-Gir dry deciduous forests',
 '296': 'Narmada Valley dry deciduous forests',
 '297': 'North Deccan dry deciduous forests',
 '298': 'South Deccan Plateau dry deciduous forests',
 '299': 'Southeast Indochina dry evergreen forests',
 '300': 'Southern Vietnam lowland dry forests',
 '301': 'Sri Lanka dry-zone dry evergreen forests',
 '302': 'Himalayan subtropical pine forests',
 '303': 'Luzon tropical pine forests',
 '304': 'Northeast India-Myanmar pine forests',
 '305': 'Sumatran tropical pine forests',
 '306': 'Eastern Himalayan broadleaf forests',
 '307': 'Northern Triangle temperate forests',
 '308': 'Western Himalayan broadleaf forests',
 '309': 'Eastern Himalayan subalpine conifer forests',
 '310': 'Western Himalayan subalpine conifer forests',
 '311': 'Terai-Duar savanna and grasslands',
 '312': 'Rann of Kutch seasonal salt marsh',
 '313': 'Kinabalu montane alpine meadows',
 '314': 'Aravalli west thorn scrub forests',
 '315': 'Deccan thorn scrub forests',
 '316': 'Godavari-Krishna mangroves',
 '317': 'Indus Valley desert',
 '318': 'Thar desert',
 '319': 'Indochina mangroves',
 '320': 'Indus River Delta-Arabian Sea mangroves',
 '321': 'Myanmar Coast mangroves',
 '322': 'Sunda Shelf mangroves',
 '323': 'Sundarbans mangroves',
 '324': 'Sonoran-Sinaloan subtropical dry forest',
 '325': 'Bermuda subtropical conifer forests',
 '326': 'Sierra Madre Occidental pine-oak forests',
 '327': 'Sierra Madre Oriental pine-oak forests',
 '328': 'Allegheny Highlands forests',
 '329': 'Appalachian mixed mesophytic forests',
 '330': 'Appalachian Piedmont forests',
 '331': 'Appalachian-Blue Ridge forests',
 '332': 'East Central Texas forests',
 '333': 'Eastern Canadian Forest-Boreal transition',
 '334': 'Eastern Great Lakes lowland forests',
 '335': 'Gulf of St. Lawrence lowland forests',
 '336': 'Interior Plateau US Hardwood Forests',
 '337': 'Mississippi lowland forests',
 '338': 'New England-Acadian forests',
 '339': 'Northeast US Coastal forests',
 '340': 'Ozark Highlands mixed forests',
 '341': 'Ozark Mountain forests',
 '342': 'Southern Great Lakes forests',
 '343': 'Upper Midwest US forest-savanna transition',
 '344': 'Western Great Lakes forests',
 '345': 'Alberta-British Columbia foothills forests',
 '346': 'Arizona Mountains forests',
 '347': 'Atlantic coastal pine barrens',
 '348': 'Blue Mountains forests',
 '349': 'British Columbia coastal conifer forests',
 '350': 'Central British Columbia Mountain forests',
 '351': 'Central Pacific Northwest coastal forests',
 '352': 'Central-Southern Cascades Forests',
 '353': 'Colorado Rockies forests',
 '354': 'Eastern Cascades forests',
 '355': 'Fraser Plateau and Basin conifer forests',
 '356': 'Great Basin montane forests',
 '357': 'Klamath-Siskiyou forests',
 '358': 'North Cascades conifer forests',
 '359': 'Northern California coastal forests',
 '360': 'Northern Pacific Alaskan coastal forests',
 '361': 'Northern Rockies conifer forests',
 '362': 'Okanogan dry forests',
 '363': 'Piney Woods',
 '364': 'Puget lowland forests',
 '365': 'Queen Charlotte Islands conifer forests',
 '366': 'Sierra Nevada forests',
 '367': 'South Central Rockies forests',
 '368': 'Wasatch and Uinta montane forests',
 '369': 'Alaska Peninsula montane taiga',
 '370': 'Central Canadian Shield forests',
 '371': 'Cook Inlet taiga',
 '372': 'Copper Plateau taiga',
 '373': 'Eastern Canadian forests',
 '374': 'Eastern Canadian Shield taiga',
 '375': 'Interior Alaska-Yukon lowland taiga',
 '376': 'Mid-Canada Boreal Plains forests',
 '377': 'Midwest Canadian Shield forests',
 '378': 'Muskwa-Slave Lake taiga',
 '379': 'Northern Canadian Shield taiga',
 '380': 'Northern Cordillera forests',
 '381': 'Northwest Territories taiga',
 '382': 'Southern Hudson Bay taiga',
 '383': 'Watson Highlands taiga',
 '384': 'Western Gulf coastal grasslands',
 '385': 'California Central Valley grasslands',
 '386': 'Canadian Aspen forests and parklands',
 '387': 'Central US forest-grasslands transition',
 '388': 'Central Tallgrass prairie',
 '389': 'Central-Southern US mixed grasslands',
 '390': 'Cross-Timbers savanna-woodland',
 '391': 'Edwards Plateau savanna',
 '392': 'Flint Hills tallgrass prairie',
 '393': 'Mid-Atlantic US coastal savannas',
 '394': 'Montana Valley and Foothill grasslands',
 '395': 'Nebraska Sand Hills mixed grasslands',
 '396': 'Northern Shortgrass prairie',
 '397': 'Northern Tallgrass prairie',
 '398': 'Palouse prairie',
 '399': 'Southeast US conifer savannas',
 '400': 'Southeast US mixed woodlands and savannas',
 '401': 'Texas blackland prairies',
 '402': 'Western shortgrass prairie',
 '403': 'Willamette Valley oak savanna',
 '404': 'Ahklun and Kilbuck Upland Tundra',
 '405': 'Alaska-St. Elias Range tundra',
 '406': 'Aleutian Islands tundra',
 '407': 'Arctic coastal tundra',
 '408': 'Arctic foothills tundra',
 '409': 'Beringia lowland tundra',
 '410': 'Beringia upland tundra',
 '411': 'Brooks-British Range tundra',
 '412': 'Canadian High Arctic tundra',
 '413': 'Canadian Low Arctic tundra',
 '414': 'Canadian Middle Arctic Tundra',
 '415': 'Davis Highlands tundra',
 '416': 'Interior Yukon-Alaska alpine tundra',
 '417': 'Kalaallit Nunaat Arctic steppe',
 '418': 'Kalaallit Nunaat High Arctic tundra',
 '419': 'Ogilvie-MacKenzie alpine tundra',
 '420': 'Pacific Coastal Mountain icefields and tundra',
 '421': 'Torngat Mountain tundra',
 '422': 'California coastal sage and chaparral',
 '423': 'California interior chaparral and woodlands',
 '424': 'California montane chaparral and woodlands',
 '425': 'Santa Lucia Montane Chaparral and Woodlands',
 '426': 'Baja California desert',
 '427': 'Central Mexican matorral',
 '428': 'Chihuahuan desert',
 '429': 'Colorado Plateau shrublands',
 '430': 'Great Basin shrub steppe',
 '431': 'Gulf of California xeric scrub',
 '432': 'Meseta Central matorral',
 '433': 'Mojave desert',
 '434': 'Snake-Columbia shrub steppe',
 '435': 'Sonoran desert',
 '436': 'Tamaulipan matorral',
 '437': 'Tamaulipan mezquital',
 '438': 'Wyoming Basin shrub steppe',
 '439': 'Alto Paraná Atlantic forests',
 '440': 'Araucaria moist forests',
 '441': 'Atlantic Coast restingas',
 '442': 'Bahia coastal forests',
 '443': 'Bahia interior forests',
 '444': 'Bolivian Yungas',
 '445': 'Caatinga Enclaves moist forests',
 '446': 'Caqueta moist forests',
 '447': 'Catatumbo moist forests',
 '448': 'Cauca Valley montane forests',
 '449': 'Cayos Miskitos-San Andrés and Providencia moist forests',
 '450': 'Central American Atlantic moist forests',
 '451': 'Central American montane forests',
 '452': 'Chiapas montane forests',
 '453': 'Chimalapas montane forests',
 '454': 'Chocó-Darién moist forests',
 '455': 'Cocos Island moist forests',
 '456': 'Cordillera La Costa montane forests',
 '457': 'Cordillera Oriental montane forests',
 '458': 'Costa Rican seasonal moist forests',
 '459': 'Cuban moist forests',
 '460': 'Eastern Cordillera Real montane forests',
 '461': 'Eastern Panamanian montane forests',
 '462': 'Fernando de Noronha-Atol das Rocas moist forests',
 '463': 'Guianan freshwater swamp forests',
 '464': 'Guianan Highlands moist forests',
 '465': 'Guianan lowland moist forests',
 '466': 'Guianan piedmont moist forests',
 '467': 'Gurupa várzea',
 '468': 'Hispaniolan moist forests',
 '469': 'Iquitos várzea',
 '470': 'Isthmian-Atlantic moist forests',
 '471': 'Isthmian-Pacific moist forests',
 '472': 'Jamaican moist forests',
 '473': 'Japurá-Solimões-Negro moist forests',
 '474': 'Juruá-Purus moist forests',
 '475': 'Leeward Islands moist forests',
 '476': 'Madeira-Tapajós moist forests',
 '477': 'Magdalena Valley montane forests',
 '478': 'Magdalena-Urabá moist forests',
 '479': 'Marañón dry forests',
 '480': 'Marajó várzea',
 '481': 'Mato Grosso tropical dry forests',
 '482': 'Monte Alegre várzea',
 '483': 'Napo moist forests',
 '484': 'Negro-Branco moist forests',
 '485': 'Northeast Brazil restingas',
 '486': 'Northwest Andean montane forests',
 '487': 'Oaxacan montane forests',
 '488': 'Orinoco Delta swamp forests',
 '489': 'Pantanos de Centla',
 '490': 'Pantepui forests and shrublands',
 '491': 'Pernambuco coastal forests',
 '492': 'Pernambuco interior forests',
 '493': 'Peruvian Yungas',
 '494': 'Petén-Veracruz moist forests',
 '495': 'Puerto Rican moist forests',
 '496': 'Purus várzea',
 '497': 'Purus-Madeira moist forests',
 '498': 'Rio Negro campinarana',
 '499': 'Santa Marta montane forests',
 '500': 'Serra do Mar coastal forests',
 '501': 'Sierra de los Tuxtlas',
 '502': 'Sierra Madre de Chiapas moist forests',
 '503': 'Solimões-Japurá moist forests',
 '504': 'Southern Andean Yungas',
 '505': 'Southwest Amazon moist forests',
 '506': 'Talamancan montane forests',
 '507': 'Tapajós-Xingu moist forests',
 '508': 'Tocantins/Pindare moist forests',
 '509': 'Trindade-Martin Vaz Islands tropical forests',
 '510': 'Trinidad and Tobago moist forest',
 '511': 'Uatumã-Trombetas moist forests',
 '512': 'Ucayali moist forests',
 '513': 'Venezuelan Andes montane forests',
 '514': 'Veracruz moist forests',
 '515': 'Veracruz montane forests',
 '516': 'Western Ecuador moist forests',
 '517': 'Windward Islands moist forests',
 '518': 'Xingu-Tocantins-Araguaia moist forests',
 '519': 'Yucatán moist forests',
 '520': 'Apure-Villavicencio dry forests',
 '521': 'Bajío dry forests',
 '522': 'Balsas dry forests',
 '523': 'Bolivian montane dry forests',
 '524': 'Brazilian Atlantic dry forests',
 '525': 'Caatinga',
 '526': 'Cauca Valley dry forests',
 '527': 'Central American dry forests',
 '528': 'Chiapas Depression dry forests',
 '529': 'Chiquitano dry forests',
 '530': 'Cuban dry forests',
 '531': 'Ecuadorian dry forests',
 '532': 'Hispaniolan dry forests',
 '533': 'Islas Revillagigedo dry forests',
 '534': 'Jalisco dry forests',
 '535': 'Jamaican dry forests',
 '536': 'Lara-Falcón dry forests',
 '537': 'Lesser Antillean dry forests',
 '538': 'Magdalena Valley dry forests',
 '539': 'Maracaibo dry forests',
 '540': 'Maranhão Babaçu forests',
 '541': 'Panamanian dry forests',
 '542': 'Patía valley dry forests',
 '543': 'Puerto Rican dry forests',
 '544': 'Sierra de la Laguna dry forests',
 '545': 'Sinaloan dry forests',
 '546': 'Sinú Valley dry forests',
 '547': 'Southern Pacific dry forests',
 '548': 'Trinidad and Tobago dry forest',
 '549': 'Tumbes-Piura dry forests',
 '550': 'Veracruz dry forests',
 '551': 'Yucatán dry forests',
 '552': 'Bahamian pineyards',
 '553': 'Central American pine-oak forests',
 '554': 'Cuban pine forests',
 '555': 'Hispaniolan pine forests',
 '556': 'Sierra de la Laguna pine-oak forests',
 '557': 'Sierra Madre de Oaxaca pine-oak forests',
 '558': 'Sierra Madre del Sur pine-oak forests',
 '559': 'Trans-Mexican Volcanic Belt pine-oak forests',
 '560': 'Juan Fernández Islands temperate forests',
 '561': 'Magellanic subpolar forests',
 '562': 'San Félix-San Ambrosio Islands temperate forests',
 '563': 'Valdivian temperate forests',
 '564': 'Belizian pine savannas',
 '565': 'Beni savanna',
 '566': 'Campos Rupestres montane savanna',
 '567': 'Cerrado',
 '568': 'Clipperton Island shrub and grasslands',
 '569': 'Dry Chaco',
 '570': 'Guianan savanna',
 '571': 'Humid Chaco',
 '572': 'Llanos',
 '573': 'Miskito pine forests',
 '574': 'Uruguayan savanna',
 '575': 'Espinal',
 '576': 'Humid Pampas',
 '577': 'Low Monte',
 '578': 'Patagonian steppe',
 '579': 'Cuban wetlands',
 '580': 'Enriquillo wetlands',
 '581': 'Everglades flooded grasslands',
 '582': 'Guayaquil flooded grasslands',
 '583': 'Orinoco wetlands',
 '584': 'Pantanal',
 '585': 'Paraná flooded savanna',
 '586': 'Southern Cone Mesopotamian savanna',
 '587': 'Central Andean dry puna',
 '588': 'Central Andean puna',
 '589': 'Central Andean wet puna',
 '590': 'Cordillera Central páramo',
 '591': 'Cordillera de Merida páramo',
 '592': 'High Monte',
 '593': 'Northern Andean páramo',
 '594': 'Santa Marta páramo',
 '595': 'Southern Andean steppe',
 '596': 'Chilean Matorral',
 '597': 'Araya and Paria xeric scrub',
 '598': 'Atacama desert',
 '599': 'Caribbean shrublands',
 '600': 'Cuban cactus scrub',
 '601': 'Galápagos Islands xeric scrub',
 '602': 'Guajira-Barranquilla xeric scrub',
 '603': 'La Costa xeric shrublands',
 '604': 'Malpelo Island xeric scrub',
 '605': 'Motagua Valley thornscrub',
 '606': 'Paraguaná xeric scrub',
 '607': 'San Lucan xeric scrub',
 '608': 'Sechura desert',
 '609': 'St. Peter and St. Paul Rocks',
 '610': 'Tehuacán Valley matorral',
 '611': 'Amazon-Orinoco-Southern Caribbean mangroves',
 '612': 'Bahamian-Antillean mangroves',
 '613': 'Mesoamerican Gulf-Caribbean mangroves',
 '614': 'Northern Mesoamerican Pacific mangroves',
 '615': 'South American Pacific mangroves',
 '616': 'Southern Atlantic Brazilian mangroves',
 '617': 'Southern Mesoamerican Pacific mangroves',
 '618': 'Carolines tropical moist forests',
 '619': 'Central Polynesian tropical moist forests',
 '620': 'Cook Islands tropical moist forests',
 '621': 'Eastern Micronesia tropical moist forests',
 '622': 'Fiji tropical moist forests',
 '623': "Hawai'i tropical moist forests",
 '624': 'Kermadec Islands subtropical moist forests',
 '625': 'Marquesas tropical moist forests',
 '626': 'Ogasawara subtropical moist forests',
 '627': 'Palau tropical moist forests',
 '628': 'Rapa Nui and Sala y Gómez subtropical forests',
 '629': 'Samoan tropical moist forests',
 '630': 'Society Islands tropical moist forests',
 '631': 'Tongan tropical moist forests',
 '632': 'Tuamotu tropical moist forests',
 '633': 'Tubuai tropical moist forests',
 '634': 'Western Polynesian tropical moist forests',
 '635': 'Fiji tropical dry forests',
 '636': "Hawai'i tropical dry forests",
 '637': 'Marianas tropical dry forests',
 '638': 'Yap tropical dry forests',
 '639': "Hawai'i tropical high shrublands",
 '640': "Hawai'i tropical low shrublands",
 '641': "Northwest Hawai'i scrub",
 '642': 'Guizhou Plateau broadleaf and mixed forests',
 '643': 'Yunnan Plateau subtropical evergreen forests',
 '644': 'Appenine deciduous montane forests',
 '645': 'Azores temperate mixed forests',
 '646': 'Balkan mixed forests',
 '647': 'Baltic mixed forests',
 '648': 'Cantabrian mixed forests',
 '649': 'Caspian Hyrcanian mixed forests',
 '650': 'Caucasus mixed forests',
 '651': 'Celtic broadleaf forests',
 '652': 'Central Anatolian steppe and woodlands',
 '653': 'Central China Loess Plateau mixed forests',
 '654': 'Central European mixed forests',
 '655': 'Central Korean deciduous forests',
 '656': 'Changbai Mountains mixed forests',
 '657': 'Changjiang Plain evergreen forests',
 '658': 'Crimean Submediterranean forest complex',
 '659': 'Daba Mountains evergreen forests',
 '660': 'Dinaric Mountains mixed forests',
 '661': 'East European forest steppe',
 '662': 'Eastern Anatolian deciduous forests',
 '663': 'English Lowlands beech forests',
 '664': 'European Atlantic mixed forests',
 '665': 'Euxine-Colchic broadleaf forests',
 '666': 'Hokkaido deciduous forests',
 '667': 'Huang He Plain mixed forests',
 '668': 'Madeira evergreen forests',
 '669': 'Manchurian mixed forests',
 '670': 'Nihonkai evergreen forests',
 '671': 'Nihonkai montane deciduous forests',
 '672': 'North Atlantic moist mixed forests',
 '673': 'Northeast China Plain deciduous forests',
 '674': 'Pannonian mixed forests',
 '675': 'Po Basin mixed forests',
 '676': 'Pyrenees conifer and mixed forests',
 '677': 'Qin Ling Mountains deciduous forests',
 '678': 'Rodope montane mixed forests',
 '679': 'Sarmatic mixed forests',
 '680': 'Sichuan Basin evergreen broadleaf forests',
 '681': 'Southern Korea evergreen forests',
 '682': 'Taiheiyo evergreen forests',
 '683': 'Taiheiyo montane deciduous forests',
 '684': 'Tarim Basin deciduous forests and steppe',
 '685': 'Ussuri broadleaf and mixed forests',
 '686': 'Western European broadleaf forests',
 '687': 'Western Siberian hemiboreal forests',
 '688': 'Zagros Mountains forest steppe',
 '689': 'Alps conifer and mixed forests',
 '690': 'Altai montane forest and forest steppe',
 '691': 'Caledon conifer forests',
 '692': 'Carpathian montane forests',
 '693': 'Da Hinggan-Dzhagdy Mountains conifer forests',
 '694': 'East Afghan montane conifer forests',
 '695': 'Elburz Range forest steppe',
 '696': 'Helanshan montane conifer forests',
 '697': 'Hengduan Mountains subalpine conifer forests',
 '698': 'Hokkaido montane conifer forests',
 '699': 'Honshu alpine conifer forests',
 '700': 'Khangai Mountains conifer forests',
 '701': 'Mediterranean conifer and mixed forests',
 '702': 'Northeast Himalayan subalpine conifer forests',
 '703': 'Northern Anatolian conifer and deciduous forests',
 '704': 'Nujiang Langcang Gorge alpine conifer and mixed forests',
 '705': 'Qilian Mountains conifer forests',
 '706': 'Qionglai-Minshan conifer forests',
 '707': 'Sayan montane conifer forests',
 '708': 'Scandinavian coastal conifer forests',
 '709': 'Tian Shan montane conifer forests',
 '710': 'East Siberian taiga',
 '711': 'Iceland boreal birch forests and alpine tundra',
 '712': 'Kamchatka taiga',
 '713': 'Kamchatka-Kurile meadows and sparse forests',
 '714': 'Northeast Siberian taiga',
 '715': 'Okhotsk-Manchurian taiga',
 '716': 'Sakhalin Island taiga',
 '717': 'Scandinavian and Russian taiga',
 '718': 'Trans-Baikal conifer forests',
 '719': 'Urals montane forest and taiga',
 '720': 'West Siberian taiga',
 '721': 'Alai-Western Tian Shan steppe',
 '722': 'Al-Hajar foothill xeric woodlands and shrublands',
 '723': 'Al-Hajar montane woodlands and shrublands',
 '724': 'Altai steppe and semi-desert',
 '725': 'Central Anatolian steppe',
 '726': 'Daurian forest steppe',
 '727': 'Eastern Anatolian montane steppe',
 '728': 'Emin Valley steppe',
 '729': 'Faroe Islands boreal grasslands',
 '730': 'Gissaro-Alai open woodlands',
 '731': 'Kazakh forest steppe',
 '732': 'Kazakh steppe',
 '733': 'Kazakh upland steppe',
 '734': 'Mongolian-Manchurian grassland',
 '735': 'Pontic steppe',
 '736': 'Sayan Intermontane steppe',
 '737': 'Selenge-Orkhon forest steppe',
 '738': 'South Siberian forest steppe',
 '739': 'Syrian xeric grasslands and shrublands',
 '740': 'Tian Shan foothill arid steppe',
 '741': 'Amur meadow steppe',
 '742': 'Bohai Sea saline meadow',
 '743': 'Nenjiang River grassland',
 '744': 'Nile Delta flooded savanna',
 '745': 'Saharan halophytics',
 '746': 'Suiphun-Khanka meadows and forest meadows',
 '747': 'Tigris-Euphrates alluvial salt marsh',
 '748': 'Yellow Sea saline meadow',
 '749': 'Altai alpine meadow and tundra',
 '750': 'Central Tibetan Plateau alpine steppe',
 '751': 'Eastern Himalayan alpine shrub and meadows',
 '752': 'Ghorat-Hazarajat alpine meadow',
 '753': 'Hindu Kush alpine meadow',
 '754': 'Karakoram-West Tibetan Plateau alpine steppe',
 '755': 'Khangai Mountains alpine meadow',
 '756': 'Kopet Dag woodlands and forest steppe',
 '757': 'Kuh Rud and Eastern Iran montane woodlands',
 '758': 'Mediterranean High Atlas juniper steppe',
 '759': 'North Tibetan Plateau-Kunlun Mountains alpine desert',
 '760': 'Northwestern Himalayan alpine shrub and meadows',
 '761': 'Ordos Plateau steppe',
 '762': 'Pamir alpine desert and tundra',
 '763': 'Qilian Mountains subalpine meadows',
 '764': 'Sayan alpine meadows and tundra',
 '765': 'Southeast Tibet shrublands and meadows',
 '766': 'Sulaiman Range alpine meadows',
 '767': 'Tian Shan montane steppe and meadows',
 '768': 'Tibetan Plateau alpine shrublands and meadows',
 '769': 'Western Himalayan alpine shrub and meadows',
 '770': 'Yarlung Zanbo arid steppe',
 '771': 'Cherskii-Kolyma mountain tundra',
 '772': 'Chukchi Peninsula tundra',
 '773': 'Kamchatka tundra',
 '774': 'Kola Peninsula tundra',
 '775': 'Northeast Siberian coastal tundra',
 '776': 'Northwest Russian-Novaya Zemlya tundra',
 '777': 'Novosibirsk Islands Arctic desert',
 '778': 'Russian Arctic desert',
 '779': 'Russian Bering tundra',
 '780': 'Scandinavian Montane Birch forest and grasslands',
 '781': 'Taimyr-Central Siberian tundra',
 '782': 'Trans-Baikal Bald Mountain tundra',
 '783': 'Wrangel Island Arctic desert',
 '784': 'Yamal-Gydan tundra',
 '785': 'Aegean and Western Turkey sclerophyllous and mixed forests',
 '786': 'Anatolian conifer and deciduous mixed forests',
 '787': 'Canary Islands dry woodlands and forests',
 '788': 'Corsican montane broadleaf and mixed forests',
 '789': 'Crete Mediterranean forests',
 '790': 'Cyprus Mediterranean forests',
 '791': 'Eastern Mediterranean conifer-broadleaf forests',
 '792': 'Iberian conifer forests',
 '793': 'Iberian sclerophyllous and semi-deciduous forests',
 '794': 'Illyrian deciduous forests',
 '795': 'Italian sclerophyllous and semi-deciduous forests',
 '796': 'Mediterranean Acacia-Argania dry woodlands and succulent thickets',
 '797': 'Mediterranean dry woodlands and steppe',
 '798': 'Mediterranean woodlands and forests',
 '799': 'Northeast Spain and Southern France Mediterranean forests',
 '800': 'Northwest Iberian montane forests',
 '801': 'Pindus Mountains mixed forests',
 '802': 'South Apennine mixed montane forests',
 '803': 'Southeast Iberian shrubs and woodlands',
 '804': 'Southern Anatolian montane conifer and deciduous forests',
 '805': 'Southwest Iberian Mediterranean sclerophyllous and mixed forests',
 '806': 'Tyrrhenian-Adriatic sclerophyllous and mixed forests',
 '807': 'Afghan Mountains semi-desert',
 '808': 'Alashan Plateau semi-desert',
 '809': 'Arabian desert',
 '810': 'Arabian sand desert',
 '811': 'Arabian-Persian Gulf coastal plain desert',
 '812': 'Azerbaijan shrub desert and steppe',
 '813': 'Badghyz and Karabil semi-desert',
 '814': 'Baluchistan xeric woodlands',
 '815': 'Caspian lowland desert',
 '816': 'Central Afghan Mountains xeric woodlands',
 '817': 'Central Asian northern desert',
 '818': 'Central Asian riparian woodlands',
 '819': 'Central Asian southern desert',
 '820': 'Central Persian desert basins',
 '821': 'East Arabian fog shrublands and sand desert',
 '822': 'East Sahara Desert',
 '823': 'East Saharan montane xeric woodlands',
 '824': 'Eastern Gobi desert steppe',
 '825': 'Gobi Lakes Valley desert steppe',
 '826': 'Great Lakes Basin desert steppe',
 '827': 'Junggar Basin semi-desert',
 '828': 'Kazakh semi-desert',
 '829': 'Kopet Dag semi-desert',
 '830': 'Mesopotamian shrub desert',
 '831': 'North Arabian desert',
 '832': 'North Arabian highland shrublands',
 '833': 'North Saharan Xeric Steppe and Woodland',
 '834': 'Paropamisus xeric woodlands',
 '835': 'Qaidam Basin semi-desert',
 '836': 'Red Sea coastal desert',
 '837': 'Red Sea-Arabian Desert shrublands',
 '838': 'Registan-North Pakistan sandy desert',
 '839': 'Saharan Atlantic coastal desert',
 '840': 'South Arabian plains and plateau desert',
 '841': 'South Iran Nubo-Sindian desert and semi-desert',
 '842': 'South Sahara desert',
 '843': 'Taklimakan desert',
 '844': 'Tibesti-Jebel Uweinat montane xeric woodlands',
 '845': 'West Sahara desert',
 '846': 'West Saharan montane xeric woodlands'}

biomeNum_2_biomeName = {
 '1': 'Tropical and Subtropical Moist Broadleaf Forests',
 '2': 'Tropical and Subtropical Dry Broadleaf Forests',
 '3': 'Tropical and Subtropical Coniferous Forests',
 '4': 'Temperate Broadleaf and Mixed Forests',
 '5': 'Temperate Conifer Forests',
 '6': 'Boreal Forests/Taiga',
 '7': 'Tropical and Subtropical Grasslands, Savannas and Shrublands',
 '8': 'Temperate Grasslands, Savannas and Shrublands',
 '9': 'Flooded Grasslands and Savannas',
 '10': 'Montane Grasslands and Shrublands',
 '11': 'Tundra',
 '12': 'Mediterranean Forests, Woodlands and Scrub',
 '13': 'Deserts and Xeric Shrublands',
 '14': 'Mangroves'}