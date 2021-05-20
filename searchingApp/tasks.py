from celery import shared_task
from .models import YoutubeData
from django.conf import settings
import requests
import datetime

@shared_task
def add(x=2,y=3):
    print(x+y)
    return x+y

@shared_task
def insert_into_database(recordsAsDictionary):
    for videoid in recordsAsDictionary:
        if not YoutubeData.objects.filter(video_id=videoid).exists():
            video_instance = YoutubeData(video_id=videoid,published_date=recordsAsDictionary[videoid]['published_at'], title=recordsAsDictionary[videoid]['title'], description=recordsAsDictionary[videoid]['description'], actual_link=recordsAsDictionary[videoid]['url'])
            video_instance.save()
    return 1

@shared_task
def fetch_youtube_data(n = 10,query='celery videos', Async_run=True):
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

    if Async_run:
        insert_into_database.delay(records)
    else:
        insert_into_database(records)

    return records