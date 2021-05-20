from django.db import models

# Create your models here.
class YoutubeData(models.Model):
    video_id = models.CharField(max_length=255, db_index=True)
    published_date = models.DateField()
    title = models.TextField()
    description = models.TextField()
    actual_link = models.CharField(max_length=255)

    def __str__(self):
        return self.title