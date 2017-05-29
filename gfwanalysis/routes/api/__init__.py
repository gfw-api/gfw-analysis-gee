from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime

from flask import jsonify

# GENERIC Error


def error(status=500, detail='Generic Error'):
    error = {
        'status': status,
        'detail': detail
    }
    return jsonify(errors=[error]), status


def set_params(request):
    """-"""
    threshold = request.args.get('thresh', 30)
    begin = request.args.get('begin', '2001-01-01')
    end = request.args.get('end', '2013-01-01')
    period = request.args.get('period', None)
    if period and len(period.split(',')) > 1:
        first = period.split(',')[0]
        second = period.split(',')[1]
        try:
            if len(first.split('-')) > 2 and len(second.split('-')) > 2:
                datetime.datetime(year=int(first.split('-')[0]), month=int(first.split('-')[1]), day=int(first.split('-')[2]))
                datetime.datetime(year=int(second.split('-')[0]), month=int(second.split('-')[1]), day=int(second.split('-')[2]))
                begin = first
                end = second
            else:
                pass
        except Exception:
            pass
    else:
        pass
    return threshold, begin, end
