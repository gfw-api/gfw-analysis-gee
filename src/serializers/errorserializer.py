from models.error import Error, ErrorSchema

def serialize(status, error_message):
  error = Error(status=status, detail=error_message)
  errors = [error] # make it iterable so response can contain a list of errs
  response = ErrorSchema(many=True).dump(errors)
  return {'errors': response.data} # particular dict response
