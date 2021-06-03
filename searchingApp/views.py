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
from pymodm.errors import DoesNotExist
from youtubeRecords.settings import get_elastic_instance
import pymongo


def getUser(key_name):
    secret_key = getValue(key_name + "_secret")
    token = getValue(key_name + "_access")

    if secret_key and token:
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('UnAuthenticated! Session has been expired Login Again Please') 

        try:
            return User.objects.raw({ "_id" : payload['id']} ).first()
        except DoesNotExist:
            return None
    else:
        return None



class topicRegistration(APIView):
    def post(self, request):
        query = request.data.get('query')
        numberOfVideos = request.data.get('videos_n')

        if not query or query.isspace():
            return Response({"message" : "query not specified"}, status=status.HTTP_403_FORBIDDEN)

        if not numberOfVideos:
            numberOfVideos = 10
        
        # query = query.lower()
        current_user = getUser(request.COOKIES.get('jwt'))
        if current_user:
            somedata = fetch_youtube_data.delay(current_user.serialize(), numberOfVideos, query)
            return Response({"message" : "done"}, status=status.HTTP_201_CREATED)
        return Response({"message" : "Already Registered"}, status=status.HTTP_208_ALREADY_REPORTED)


class bulkRegistration(APIView):

    def get(self, request):
        """
        
                # queries, n
                # store with jwt key, query -> n
                # find all saved queries
                # check for number of videos > n
        
        
        
        """

        all_queries = request.data.get('queries')
        current_user_key = request.COOKIES.get('jwt')
        limit = int(request.GET.get('limit',"1"))
        offset = int(request.GET.get('offset',"0"))
        
        # if asked videos < 0
        if limit < 0 or offset < 0:
            return Response({"message" : "Number of videos cann't be smaller than 0"}, status=status.HTTP_400_BAD_REQUEST)


        if all_queries:
            current_user = getUser(current_user_key)
            # all_queries = [queries.lower() for queries in all_queries]
            try:
                saved_queries = queryModel.objects.aggregate(
						{ "$match" : {"$and" : [{ "query" : {"$in" : all_queries }},{"user" : current_user.email }]}}, 
                        {"$sort" : { "query_lasttime" :  -1 } },
				        {"$project" : { "_id": 0, "query" : 1, "videos" : 1}},
                        {"$skip" : offset},
                        {"$limit" : limit+1}
					)

                
                bulk_response = list(saved_queries)
                saved_queries = []
                # return Response(bulk_response)

                next_link = "No More queries"
                if len(bulk_response) == limit+1:
                    next_link = f"offset={offset+limit}&limit={limit}" 
                    bulk_response = bulk_response[:limit] 
                                    
                for document in bulk_response:
                    saved_queries.append(document["query"])


            except DoesNotExist:
                saved_queries = []


            for query in all_queries:
                if query not in saved_queries:
                    records = fetch_youtube_data.delay(current_user.serialize(),n = 5 , query=query, force=True)



            return Response({ "Next Page" : next_link, "queries" : bulk_response }, status=status.HTTP_200_OK)
        return Response({"message" : "It must have queries"}, status=status.HTTP_400_BAD_REQUEST)

    
  
        
    

class searchingView(ListAPIView):

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
        current_user = getUser(request.COOKIES.get('jwt'))
        offset = int(request.GET.get('offset',"0"))
        limit = int(request.GET.get('limit',"5"))

        # if asked videos < 0
        if limit < 0 or offset < 0:
            return Response({"message" : "Number of videos cann't be smaller than 0"}, status=status.HTTP_400_BAD_REQUEST)

        # if query provided
        if query:
            try:

                queryset = queryModel.objects.aggregate(
                        { "$match" : { "query" : query,"user" : current_user.email }},
                        { "$project":
                            {
                                "_id" : 0,
                                "videos" : 1
                            }
                        },
                        {"$unwind" : { "path" : "$videos"}},
                        {"$sort" : { "videos.published_date": -1}},
                        {"$skip" : offset},
                        {"$limit" :  limit+1},
                )

                all_videos = []
                queryset = list(queryset)

                if queryset:
                    videos = [video['videos'] for video in queryset]
                    print(videos)
                    available = len(queryset)

                    if limit > available:
                        records = fetch_youtube_data(current_user.serialize(),limit,query)

                        for video_id in records:
                            all_videos.append(records[video_id])

                    else:
                        all_videos.extend(videos[:limit])  


                    next_link = "No More Videos"
                    if available == limit+1:
                        next_link = f"offset={offset+limit}&limit={limit}"  
                                        

                    final_solution = {
                        "next_link" : next_link,
                        "videos" : all_videos
                    }
                    return Response(final_solution,status=status.HTTP_200_OK)
                
                else:
                    records = fetch_youtube_data(current_user.serialize(),limit,query)
                    return Response(records, status=status.HTTP_200_OK)
            
            except DoesNotExist:
            # if query doesnt exists
                records = fetch_youtube_data(current_user.serialize(),limit,query,force=True)
                return Response(records, status=status.HTTP_200_OK)
        
        # if user didnt enter query
        return Response({"error" : "query not specified"}, status=status.HTTP_400_BAD_REQUEST)
            

class textSearch(APIView):
    def get(self, request):
        keyword = request.GET.get('keyword')

        if keyword:
            search_query = {
                "query" : {
                    "match" : {
                        "title" : keyword
                    }
                }
            }
            
            elastic_instance = get_elastic_instance()
            response = elastic_instance.search(index='youtubevideos', body=search_query)

            return Response(response, status=status.HTTP_200_OK)
        return Response({"message" : "No keyword specified!!"}, status.HTTP_400_BAD_REQUEST)


class videosWithDateFilter(APIView):
    def get(self, request):

        start_date = request.GET.get('start_date')
        final_date = request.GET.get('final_date')

        print(start_date)
        try:
            if start_date:
                start_date = datetime.datetime.strptime(start_date,'%Y-%m-%d').date()
            else:
                start_date = (datetime.datetime.now() - datetime.timedelta(weeks=10)).date()
            
            if final_date:
                final_date = datetime.datetime.strptime(final_date,'%Y-%m-%d').date()
            else:
                final_date = datetime.datetime.now().date()
        
        except Exception as e:
            print(e)
            return Response({"message" : "Date must be in yyyy-MM-dd format"}, status=status.HTTP_400_BAD_REQUEST)

        if final_date >= start_date:

            search_query = {
                "query" : {
                    "range" : {
                        "published_date" : {
                            "gte" : start_date,
                            "lte" : final_date
                        }
                    }
                }
            }

            elastic_instance = get_elastic_instance()
            response = elastic_instance.search(index='youtubevideos', body=search_query)
            return Response(response, status=status.HTTP_200_OK)

        
        return    Response({ "error" : "final date cannt be greater than start date!!"}, status=status.HTTP_400_BAD_REQUEST)


# PUT /youtubevideos/_mapping
# {
#   "properties" : {
#     "videodetails" : {
#       "properties" : {
#         "title" : { "type" : "text" },
#         "published_date" : {
#           "type" : "date",
#           "format" : "yyyy-MM-dd"
#         },
#         "RandomNumber": {"type" : "keyword" }
#       }
#     }
#   }
# }