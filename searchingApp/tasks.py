from celery import shared_task
from .models import YoutubeData, queryModel
from users.models import User
from django.conf import settings
import requests
import datetime

@shared_task
def add(x=2,y=3):
    print(x+y)
    return x+y

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
    print(f'type is : {type(recordsAsDictionary)}')
    current_user = User.objects.filter(email=recordsAsDictionary['user']).first()
    for videoid in recordsAsDictionary:
        if videoid == 'user' or videoid == 'query':
            continue

        if not YoutubeData.objects.filter(video_id=videoid).exists():
            video_instance = YoutubeData(
                            video_id=videoid,
                            published_date=recordsAsDictionary[videoid]['published_at'], 
                            title=recordsAsDictionary[videoid]['title'], 
                            description=recordsAsDictionary[videoid]['description'], 
                            actual_link=recordsAsDictionary[videoid]['url']
                        )

            video_instance.save()
            all_new_videos.append(video_instance.serialize())
        else:
            complete_list_videos.append(YoutubeData.objects.filter(video_id=videoid).first().serialize())
    
    print('video done')

    complete_list_videos.extend(all_new_videos)
    if queryModel.objects.filter(query=recordsAsDictionary['query']).filter(user=current_user).exists():
        query_object = queryModel.objects.select_for_update().filter(query=recordsAsDictionary['query']).filter(user=current_user).first()
        query_object.videos = all_new_videos
        query_object.update()
        print('found query with the user ohibited to prevent data loss due to unsaved related object and update it')
    else:
        # current_user.save()
        query_object = queryModel(
                user=current_user, 
                query=recordsAsDictionary['query'],
                videos=[video for video in complete_list_videos],
                query_lasttime=datetime.datetime.now()
            )
        print(query_object.serialize())
        query_object.save(force_insert=True)   
        print('made query inserted into dataset')     
            
    return None 

    

@shared_task
def fetch_youtube_data(userdata, n = 10,query='celery videos'):
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

    for result in results['items']:
        video_ids.append(result['id']['videoId'])
        video_id = result['id']['videoId']
        y_m_d = result['snippet']['publishedAt'].split('-')
        final_date = datetime.datetime(int(y_m_d[0]), int(y_m_d[1]), int(y_m_d[2][0:2]))

        records[video_id] = {
            'published_at' : final_date,
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
        records[v_id]['url'] = result['snippet']['thumbnails']['high']['url']
    
    records['query'] = query
    records['user'] = userdata['email']

    insert_into_database(records)
    # insert_into_database.delay(records)
    print(records)
    return records