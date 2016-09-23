
def world_validator(request):
  geostore = request.args.get('geostore')
  if geostore:
    return True
  return False


def use_validator(name):
  useTable = False
  if name == 'mining':
    useTable = 'gfw_mining'
  elif name == 'oilpalm':
    useTable = 'gfw_oil_palm'
  elif name == 'fiber':
    useTable = 'gfw_wood_fiber'
  elif name == 'logging':
    useTable = 'gfw_logging'
  return useTable

# Not needed, flask doesn't route to /wdpa/ if there is no id
def wdpa_validator():
  pass
