from models.umd import Umd, UmdSchema

def serialize(data, umd_type='world', id=None):
  umd = Umd(id=id,
           type=umd_type, 
           attributes=data)
  response = UmdSchema().dump(umd)
  return {'data': response.data} # particular dict response
