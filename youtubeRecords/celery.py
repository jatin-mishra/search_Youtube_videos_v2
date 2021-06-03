# https://nickmccullum.com/celery-django-periodic-tasks/#:~:text=This%20module%20is%20used%20to%20define%20the%20celery%20instance.&text=Then%20import%20the%20new%20Celery,start%20of%20the%20Django%20project.&text=To%20use%20the%20Celery%20Beat,Django%20projects%20settings.py%20file.
# kill -9 $(ps aux | grep celery | grep -v grep | awk '{print $2}' | tr '\n'  ' ') > /dev/null 2>&1  : to stop all celery services
# pkill -f "celery worker"  
# redis-server --daemonize yes  
# redis-cli ping
# celery -A youtubeRecords beat -l info --logfile=celery.beat.log --detach  
# celery -A youtubeRecords worker -l info --logfile=celery.log --detach


from __future__ import absolute_import, unicode_literals
import os


from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'youtubeRecords.settings')

app = Celery('youtubeRecords')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()




@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'add_them_now' : {
        'task' : 'searchingApp.tasks.add',
        'schedule' : 30.0,
        'args' : (4,4,)
    },
    # 'Database_population' : {
    #     'task' : 'searchingApp.tasks.fetch_youtube_data',
    # },
}