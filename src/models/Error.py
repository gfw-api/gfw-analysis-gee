from marshmallow import Schema, fields

class Err(fields.Field):
  def __init__(self, status, detail):
    self.status = status
    self.detail = detail

class Error(object):
  def __init__(self, errors):
    self.errors = errors

class ErrSchema(Schema):
  status = fields.Integer()
  detail = fields.Str()

class ErrorSchema(Schema):
  errors = fields.Nested(ErrSchema, many=True)
