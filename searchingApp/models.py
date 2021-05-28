from pymodm import MongoModel, fields
import datetime
from pymodm.fields import ReferenceField
from pymongo import IndexModel
from pymongo.write_concern import WriteConcern 
from users.models import User
# Create your models here.

class YoutubeData(MongoModel):
	video_id = fields.CharField(primary_key=True)
	published_date = fields.DateTimeField()
	title = fields.CharField()
	description = fields.CharField()
	actual_link = fields.URLField()

	def serialize(self):
		return {
			"_id" : self.video_id,
			"published_date" : self.published_date,
			"title" : self.title,
			"description" : self.description,
			"actual_link" : self.actual_link
		}

	class Meta:
		write_concern = WriteConcern(j=True)
		connection_alias = 'manual_connection'

class queryModel(MongoModel):
	user = fields.ReferenceField(User, on_delete=ReferenceField.CASCADE)
	query = fields.CharField()
	videos = fields.EmbeddedDocumentListField(YoutubeData)
	query_lasttime = fields.DateTimeField()

	def serialize(self):
		return {
			"user" : self.user.email,
			"query" : self.query,
			"videos" : [video.video_id for video in self.videos ],
			"query_lasttime" : self.query_lasttime
		}

	class Meta:
		write_concern = WriteConcern(j=True)
		connection_alias = 'manual_connection'
		indexes=[IndexModel([ ('query' , 1), ('user' , 1)])]