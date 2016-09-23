from models.Umd import Umd, UmdSchema

def serialize(data):
  umd = Umd(id=0,
           type='world', #@TODO
           attributes=data)
  response = UmdSchema().dump(umd)
  return {'data': response.data} # particular dict response
