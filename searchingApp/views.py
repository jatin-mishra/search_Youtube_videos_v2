from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
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
from bson import json_util
import requests
import jwt
from users.models import User
from users.TokenManager import setValue, getValue, checkForExistence, scheduleExpire
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



def getUser(key_name):
    secret_key = getValue(key_name + "_secret")
    token = getValue(key_name + "_access")

    if secret_key and token:
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('UnAuthenticated! Session has been expired Login Again Please') 

        return User.objects.filter(email=payload['id']).first()
    else:
        raise AuthenticationFailed('UnAuthenticated! Session has been expired Login Again Please')



class topicRegistration(APIView):
    def post(self, request):
        query = request.data.get('query')
        numberOfVideos = request.data.get('videos_n')

        if not query or query.isspace():
            return Response({"message" : "query not specified"}, status=status.HTTP_403_FORBIDDEN)

        if not numberOfVideos:
            numberOfVideos = 10
        
        current_user = getUser(request.COOKIES.get('jwt'))
        if not queryModel.objects.filter(query=query).filter(user=current_user).exists():
            somedata = fetch_youtube_data.delay(current_user.serialize(), numberOfVideos, query)
            return Response({"message" : "done"}, status=status.HTTP_201_CREATED)
        
        return Response({"message" : "Already Registered"}, status=status.HTTP_208_ALREADY_REPORTED)


class bulkRegistration(APIView):

    user_queries = {}

    def get(self, request):
        key_name = request.COOKIES.get('jwt')
        if key_name in self.user_queries:
            current_user = getUser(key_name)
            bulk_response = {}
            for query in self.user_queries[key_name].keys():
                bulk_response[query] = []
                query_instance = queryModel.objects.filter(user=current_user).filter(query=query).first()
                print(f'{query} {self.user_queries[key_name][query]} and {query_instance.serialize()}')
                bulk_response[query] = query_instance.videos
            
            return Response(bulk_response, status=status.HTTP_200_OK)
        else:
            return Response({"message" : "You havent done any bulk registration yet!!"}, status=status.HTTP_403_FORBIDDEN)

    


    def post(self, request):
        """
        
                # queries, n
                # store with jwt key, query -> n
                # find all saved queries
                # check for number of videos > n
        
        
        
        """

        # to store user queries : [ {query, n} ]
        current_user_key = request.COOKIES.get('jwt')
        self.user_queries[current_user_key] = {}
        all_queries = request.data.get('queries')
        if all_queries:
            for query_dict in all_queries:

                # if query is space or query is not present in document
                if query_dict.get('query',' ').isspace():
                    return Response({"message" : "Queries cannt be empty"}, status=status.HTTP_403_FORBIDDEN)

                # [user_id] = { query1 : #videos1, query2 : #videos2, .... }
                self.user_queries[current_user_key][query_dict['query']] = query_dict.get('n',1)

            # current user for email
            current_user = getUser(current_user_key)

            # getting already registered queries for current user
            saved_queries = queryModel.objects.filter(user=current_user).filter(query__in=self.user_queries[current_user_key].keys()).all()

            # list of query strings, with filter videos_present >= videos_asked
            saved_queries = [query_obj.query for query_obj in saved_queries if len(query_obj.videos) >=  self.user_queries[current_user_key][query_obj.query] ]
            
            # if query not registered, go and register
            new_queries = []
            for query in self.user_queries[current_user_key].keys():
                if query not in saved_queries:
                    fetch_youtube_data(current_user.serialize(),n = self.user_queries[current_user_key][query], query=query)
                    new_queries.append(query)
            
            return Response({ "Newly Registered" : new_queries})
        
        return Response({"message" : "It must have queries"}, status=status.HTTP_400_BAD_REQUEST)

    
  
        
    

class searchingView(ListAPIView):

    def getPaginatedPage(self, records,  page=1, paginate_by=5):

        all_records = []
        for video_id in records:
            records[video_id]['published_date'] = records[video_id]['published_date'].strftime(f"%Y-%m-%d")
            all_records.append(records[video_id])
        
        paginator = Paginator(all_records, paginate_by)

        if page.isnumeric() or page[0]=='-' and page[1:].isnumeric():
            if int(page) <= 0:
                page = 1
            
        page_returning = page
        try:
            records = paginator.page(page)
        except PageNotAnInteger:
            records = paginator.page(1)
            page_returning = 1
        except EmptyPage:
            records = paginator.page(paginator.num_pages)
            page_returning = paginator.num_pages
        
        return records.object_list,paginator.num_pages, page_returning


    def get(self, request):
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

        query = request.GET.get('q')
        videos_n = request.GET.get('n',10)
        current_user = getUser(request.COOKIES.get('jwt'))
        videos_n = int(videos_n)

        # if asked videos < 0
        if videos_n < 0:
            return Response({"message" : "Number of videos cann't be smaller than 0"}, status=status.HTTP_400_BAD_REQUEST)

        # if query provided
        if query:
            queryset = queryModel.objects.filter(query=query)
            if queryset.exists():
                query_instance = queryModel.objects.filter(query=query).order_by('-query_lasttime').first()
                all_videos = {}
                videos = query_instance.serialize().get('videos')
                remained = 0

                if videos_n > len(videos):
                    records = fetch_youtube_data(current_user.serialize(),videos_n,query)
                    records.pop('query')
                    records.pop('user')
                    all_videos = records

                else:
                    for video_id in videos[:videos_n]:
                        video_instance = YoutubeData.objects.filter(video_id=video_id).first()
                        all_videos[video_id] = video_instance.serialize()
                        
                # if query wasn't there for current user then write it
                if not queryset.filter(user=current_user).exists():
                    fetch_youtube_data.delay(current_user.serialize(), videos_n, query)
                
                page = request.GET.get('page')

                all_videos, totalPages, current_page = self.getPaginatedPage(all_videos,page)
                finalAnswer = {
                    "total pages" : totalPages,
                    "current page" : current_page,
                    "data" : all_videos
                }

                return Response(finalAnswer,status=status.HTTP_200_OK)
            
            # if query doesnt exists
            records = fetch_youtube_data(current_user.serialize(),videos_n,query)
            records.pop('user')
            records.pop('query')
            page = request.GET.get('page')
            all_videos, totalPages, current_page = self.getPaginatedPage(records,page)
            finalAnswer = {
                    "total pages" : totalPages,
                    "current page" : current_page,
                    "data" : all_videos
                }
            return Response(finalAnswer, status=status.HTTP_200_OK)
        
        # if user didnt enter query
        return Response({"error" : "query not specified"}, status=status.HTTP_400_BAD_REQUEST)
            
