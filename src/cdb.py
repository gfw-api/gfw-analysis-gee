# Global Forest Watch API
# Copyright (C) 2013 World Resource Institute
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""This module supports executing CartoDB queries."""

import copy
import urllib
import logging
import requests

# CartoDB endpoint:
ENDPOINT = 'https://wri-01.cartodb.com/api/v2/sql'

def get_format(media_type):
  """Return CartoDB format for supplied GFW custorm media type."""
  tokens = media_type.split('.')
  if len(tokens) == 2:
    return ''
  else:
    return tokens[2].split('+')[0]


def get_url(query, params):
  """Return CartoDB query URL for supplied params."""
  params = copy.copy(params)
  params['q'] = query
  clean_params = {}
  for key, value in params.iteritems():
    if key in ['api_key', 'format', 'q', 'version']:
        clean_params[key] = value
  url = '%s?%s' % (ENDPOINT, urllib.urlencode(clean_params))

  # TODO: Hack
  if 'version' in clean_params:
    url = url.replace('v2', clean_params['version'])

  return str(url)


def get_body(query, params):
  """Return CartoDB payload body for supplied params."""
  params['q'] = query
  body = urllib.urlencode(params)
  return body


def execute(query, params={}):
  """Exectues supplied query on CartoDB and returns response body as JSON."""
  payload = get_body(query, params)
  r = requests.post(ENDPOINT, params=payload)
  return r.json()
