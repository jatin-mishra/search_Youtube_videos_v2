from celery import shared_task
from .models import YoutubeData, queryModel
from users.models import User
from django.conf import settings
import requests
import datetime
import random
from pymodm.errors import DoesNotExist
from youtubeRecords.settings import get_elastic_instance

@shared_task
def add(x=2,y=3):
    print(x+y)
    return x+y



def insert_into_elastic(video, video_id):


    # video title
    video_instance = {
            "title" : video['title'],
            "RandomNumber" : random.randint(1,10),
            # "published_date" : datetimevideo['published_at']
            "published_date" : video['published_at']

    }
    #  insert
    
    print('----------------------------------------------------')
    print(video_instance)
    
    elastic_instance = get_elastic_instance()
    elastic_instance.index(index='youtubevideos', id=video_id, body=video_instance)


@shared_task
def insert_into_database(recordsAsDictionary):
    """
        if video_from_api is not in YoutubeData:
            create an object
            save the object
            append into new_video_list

        else
            fetch record of video and append in complete_list
        
        after extending complete_list will have all video_objects from specific query

        if query exists in queryModel:
            fetch the query objects
            add new videos
        else:
            create query object with complete_video_list
    
    
    """
    print('time to insert')
    all_new_videos = []
    complete_list_videos = []
    # print(f'date ')

    # no need to try catch, as it will always be there
    # current_user = User.objects.raw({"_id":recordsAsDictionary['user']}).first()
    
    print("found user")
    
    for key_name in recordsAsDictionary:
        if key_name == 'user' or key_name == 'query':
            continue

        video_id = key_name
        try:
            videos_instance = YoutubeData.objects.raw({ "_id": video_id}).first()
            complete_list_videos.append(YoutubeData.objects.raw({ "_id" : video_id}).first().serialize())

        except DoesNotExist:
            video_instance = YoutubeData(
                            video_id=video_id,
                            published_date=recordsAsDictionary[video_id]['published_at'], 
                            title= recordsAsDictionary[video_id]['title'] if len(recordsAsDictionary[video_id]['title']) else "no title", 
                            description= recordsAsDictionary[video_id]['description'] if len(recordsAsDictionary[video_id]['description']) else "no description", 
                            actual_link= recordsAsDictionary[video_id]['url'] if len(recordsAsDictionary[video_id]['url']) else "http://127.0.0.1:8000/NoUrlAvailable"
                        )

            video_instance.save()
            insert_into_elastic(recordsAsDictionary[video_id],video_id)
            all_new_videos.append(video_instance.serialize())
            print(f"{video_id} inserted")
    
    print('video done')

    complete_list_videos.extend(all_new_videos)

    try:
        query_object = queryModel.objects.raw({ "query" : recordsAsDictionary['query'] , "user" : recordsAsDictionary['user']}).first()
        query_object.videos = complete_list_videos
        query_object.save()
        print('found query with the user ohibited to prevent data loss due to unsaved related object and update it')
    except DoesNotExist:
        query_object = queryModel(
                user=recordsAsDictionary['user'], 
                query=recordsAsDictionary['query'],
                videos=[video for video in complete_list_videos],
                query_lasttime=datetime.datetime.now()
            )

        print("query saved -> ")
        print(query_object.serialize())
        query_object.save()   
        print('made query inserted into dataset')     
            
    return None 



    

@shared_task
def fetch_youtube_data(userdata, n = 10,query='celery videos', force=False):
    
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    video_url = 'https://www.googleapis.com/youtube/v3/videos'
    search_params = {
        'part' : 'snippet',
        'key' : settings.YOUTUBE_DATA_API_KEY,
        'q' : query,
        'maxResults' : n,
        'type': 'video',
        'order' : 'date'
    }

    r = requests.get(search_url, params=search_params)
    video_ids = []
    results  = r.json()
    records = {}


    default_title = query
    default_description = query
    default_url = "http://127.0.0.1:8000/NoUrlAvailable"

    if results.get('items'):
        for result in results.get('items'):
            video_ids.append(result['id']['videoId'])
            video_id = result['id']['videoId']
            y_m_d = result['snippet']['publishedAt'].split('-')
            final_date = datetime.datetime(int(y_m_d[0]), int(y_m_d[1]), int(y_m_d[2][0:2]))


            if result["snippet"]["title"] is None:
                result["snippet"]["title"] = default_title
            
            if result["snippet"]["description"] is None:
                result["snippet"]["description"] = default_description     

            records[video_id] = {
                'published_at' : final_date.date(),
                'title': result["snippet"]["title"],
                'description' : result["snippet"]["description"]
            }
    

        video_params = {
            'key' : settings.YOUTUBE_DATA_API_KEY,
            'part' : 'snippet',
            'id' : ','.join(video_ids)
        }

        r = requests.get(video_url, params=video_params)
        results = r.json()['items']
        for result in results:
            v_id = result['id']
            if result['snippet']['thumbnails']['high']['url'] is None:
                result['snippet']['thumbnails']['high']['url'] = default_url
            records[v_id]['url'] = result['snippet']['thumbnails']['high']['url']
        
        records['query'] = query
        records['user'] = userdata['_id']

        # insert_into_database(records)
        
        insert_into_database(records)


        
        records.pop('user')
        records.pop('query')
        print(records)
        return records
    return {}