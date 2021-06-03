from __future__ import absolute_import
from .celery import app as celery_app
from decouple import config
from pymodm.connection import connect


# celery connection
__all__ = ('celery_app',)


# connecting to mongo
complate_mongo_url = config('MONGO_STRING') + config('MONGO_DATABASE')
connect(complate_mongo_url,alias='manual_connection')