from django.db import models
from users.models import User
from djongo import models as mongo_model


# Create your models here.
class YoutubeData(models.Model):
    video_id = models.CharField(max_length=255, primary_key=True)
    published_date = models.DateTimeField()
    title = models.TextField()
    description = models.TextField()
    actual_link = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    def serialize(self):
        return {
            'video_id' : self.video_id,
            'published_date' : self.published_date,
            'title' : self.title,
            'description' : self.description,
            'actual_link' : self.actual_link
        }


class queryModel(mongo_model.Model):
    user = mongo_model.EmailField()
    query = mongo_model.CharField(max_length=255, primary_key=True)
    videos = mongo_model.ArrayField(
                    model_container=YoutubeData
                )
    query_lasttime = mongo_model.DateTimeField(auto_now=True)



    def serialize(self):
        return {
            'user' : self.user,
            'query' : self.query,
            'videos' : [video_object['video_id'] for video_object in self.videos],
            'last_time' : self.query_lasttime
        }