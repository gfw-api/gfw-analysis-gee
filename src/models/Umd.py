from marshmallow import Schema, fields

class Umd(object):
  def __init__(self, type, attributes, id=0):
    self.id = id
    self.type = type
    self.attributes = attributes


class UmdSchema(Schema):
  id = fields.Integer()
  type = fields.Str()
  attributes = fields.Dict()
