import ee

def ImageColIntersect(geom, scale, reducer_type):
    def reducerWrapper(image):
        stats = image.reduceRegion(
            reducer=reducer_type,
            geometry=geom, 
            scale=scale, 
            maxPixels=1e18,
            bestEffort=False, 
            crs='EPSG:4326'
        )
        feat = ee.Feature(None).set(stats)
        return feat
    return reducerWrapper
