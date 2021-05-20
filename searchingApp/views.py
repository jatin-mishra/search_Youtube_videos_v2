from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import YoutubeData
from .tasks import insert_into_database,fetch_youtube_data
from .serializers import YoutubeDataSerializer
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

import datetime

from django.conf import settings
from django.http import HttpResponse
# from rest_framework.parsers import JSONParser
import json
import requests

searchingDefaultView


class searchingDefaultView(APIView):
    def get(self, request):
        n = 5
        query = request.data.get('query','')

        if query or len(YoutubeData.objects.all()) < n:
            if not n:
                n = 10
                
            if not query:
                query = 'celery tutorial'

            alldata = fetch_youtube_data(n,query, False)
            all_objects = []
            for videoid in alldata:
                if YoutubeData.objects.filter(video_id=videoid).exists():
                    video_instance = YoutubeData(video_id=videoid,published_date=alldata[videoid]['published_at'], title=alldata[videoid]['title'], description=alldata[videoid]['description'], actual_link=alldata[videoid]['url'])
                    all_objects.append(video_instance)
            serializer = YoutubeDataSerializer(all_objects, many=True)
        else:
            if not n:
                n=10
            all_records = YoutubeData.objects.all().order_by('-published_date')[:n] 
            serializer = YoutubeDataSerializer(all_records, many=True)
            

        return Response(serializer.data)

# Create your views here.

class searchingView(APIView):
    def get(self, request, n=None):
        query = request.data.get('query','')

        if query or len(YoutubeData.objects.all()) < n:
            if not n:
                n = 10
                
            if not query:
                query = 'celery tutorial'

            alldata = fetch_youtube_data(n,query, False)
            all_objects = []
            for videoid in alldata:
                if YoutubeData.objects.filter(video_id=videoid).exists():
                    video_instance = YoutubeData(video_id=videoid,published_date=alldata[videoid]['published_at'], title=alldata[videoid]['title'], description=alldata[videoid]['description'], actual_link=alldata[videoid]['url'])
                    all_objects.append(video_instance)
            serializer = YoutubeDataSerializer(all_objects, many=True)
        else:
            if not n:
                n=10
            all_records = YoutubeData.objects.all().order_by('-published_date')[:n] 
            serializer = YoutubeDataSerializer(all_records, many=True)
            

        return Response(serializer.data)
