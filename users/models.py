from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern 

# Create your models here.
class User(MongoModel):
	name = fields.CharField()
	email = fields.EmailField(primary_key=True)
	password = fields.CharField()

	def serialize(self):
		return {
			"name":self.name,
			"_id":self.email,
			"password":self.password
		}

	class Meta:
		write_concern = WriteConcern(j=True)
		connection_alias = 'manual_connection'


