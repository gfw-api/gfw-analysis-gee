import os
import json

def load_config_json(name):
  json_path = os.path.abspath(os.path.join(os.pardir,'microservice'))+'/'+name+'.json'
  with open(json_path) as data_file:
    info = json.load(data_file)
  return info


def get_args_from_request(request):
  """Helper function to get arguments"""
  args = {}
  period = request.args.get('period')
  thresh = request.args.get('thresh')

  if period:
    args['begin'] = period.split(',')[0]
    args['end'] = period.split(',')[1]
  if thresh:
    args['thresh'] = thresh

  return args


def request_is_error(status):
 first_element = str(status).split()[0][0]
 if first_element == '4' or first_element == '5':
   return True
 else:
   return False
