from rest_framework import serializers
from .models import YoutubeData

class YoutubeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeData
        fields = ['video_id','published_date', 'title','description', 'actual_link']