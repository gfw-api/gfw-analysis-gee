from models.umd import Umd, UmdSchema

def serialize(data, umd_type='world'):
  umd = Umd(id=0,
           type=umd_type, #@TODO
           attributes=data)
  response = UmdSchema().dump(umd)
  return {'data': response.data} # particular dict response
