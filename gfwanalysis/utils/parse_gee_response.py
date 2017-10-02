import logging


def flatten_area_hist(area_hist):
    out_dict = {}

    for output_group in area_hist['groups']:
        lulc_val = output_group['group']
        m2_val = 0

        for pixel_size, pixel_count in output_group['histogram'].items():
            m2_val += float(pixel_size) * pixel_count

        # convert m2 to ha
        out_dict[str(lulc_val)] = m2_val / 10000

    return out_dict
