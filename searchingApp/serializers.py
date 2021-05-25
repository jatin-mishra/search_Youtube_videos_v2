from rest_framework import serializers
from .models import YoutubeData,queryModel
from users.models import User
from users.serializers import UserSerializer

class YoutubeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeData
        fields = ['video_id','published_date', 'title','description', 'actual_link']

class queryModelSerializer(serializers.ModelSerializer):
    related_user = UserSerializer(many=True, read_only=True)
    related_video = YoutubeDataSerializer(read_only=True, many=True)

    class Meta:
        model = queryModel
        fields = '__all__'