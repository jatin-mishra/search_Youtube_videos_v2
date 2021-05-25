from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import YoutubeData, queryModel
from .tasks import insert_into_database,fetch_youtube_data
from django.http import JsonResponse
from rest_framework import status
import datetime
from django.conf import settings
from django.http import HttpResponse
# from rest_framework.parsers import JSONParser
import json
import requests
import jwt
from users.models import User
from users.TokenManager import setValue, getValue, checkForExistence, scheduleExpire


def getUser(key_name):
    secret_key = getValue(key_name + "_secret")
    token = getValue(key_name + "_access")

    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('UnAuthenticated! Session has been expired Login Again Please') 

    return User.objects.filter(email=payload['id']).first()


class topicRegistration(APIView):
    def post(self, request):
        query = request.data.get('query')
        numberOfVideos = request.data.get('videos_n')

        if not query:
            return Response({"message" : "query not specified"}, status=status.HTTP_400_BAD_REQUEST)

        if not numberOfVideos:
            numberOfVideos = 10
        
        current_user = getUser(request.COOKIES.get('jwt'))
        if not queryModel.objects.filter(query=query).filter(user=current_user).exists():
            somedata = fetch_youtube_data.delay(current_user.serialize(), numberOfVideos, query)
            # somedata = fetch_youtube_data(current_user.serialize(), numberOfVideos, query)
            return Response({"message" : "done"}, status=status.HTTP_201_CREATED)
        
        return Response({"message" : "Already Registered"}, status=status.HTTP_208_ALREADY_REPORTED)

# Create your views here.

class searchingView(APIView):
    def post(self, request):
        """
            if user gave a query:
                if query is present in queryModel:
                    return videos
                    add object with currentuser if not present
                else:
                    fetch the query and all
            else:
                ask for query
        
        """

        query = request.data['query']
        videos_n = request.data.get('videos_n',10)
        current_user = getUser(request.COOKIES.get('jwt'))

        print(f'videos :  {videos_n}')



        if query:
            print(f'query : {query}')
            queryset = queryModel.objects.filter(query=query)
            if queryset.exists():
                print(f' query {query} exists')
                query_instance = queryModel.objects.filter(query=query).order_by('-query_lasttime').first()
                all_videos = {}
                for video_id in query_instance.serialize().get('videos')[:videos_n]:
                    video_instance = YoutubeData.objects.filter(video_id=video_id).first()
                    all_videos[video_id] = video_instance.serialize()
                
                if not queryset.filter(user=current_user).exists():
                    fetch_youtube_data(current_user.serialize(), videos_n, query)
                    # fetch_youtube_data.delay(current_user.serialize(), video_n, query)
                    print(f'other user than {current_user.email} called for this')
                
                return Response(all_videos)
            
            # else fetch the query result
            print('fetching the data')
            records = fetch_youtube_data(current_user.serialize(),videos_n,query)
            records.pop('user')
            records.pop('query')
            return Response(records)
        


            # insert into queryModel
            # insert into videos
        return Response({"error" : "query not specified"}, status=status.HTTP_400_BAD_REQUEST)
            
