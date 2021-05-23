import redis
from datetime import timedelta
import time
import json

redis_host = "localhost"
redis_port = 6379
redis_password = ""

r = redis.StrictRedis(host=redis_host,port=redis_port, password=redis_password, decode_responses=True)

def setValue(key, value, ageInSeconds):
    r.set(key,value)
    r.expire(key,timedelta(seconds=ageInSeconds))
    print(r.get(key))


def getValue(key):
    print('trying')
    return r.get(key)


def checkForExistence(key):
    return r.exists(key)

def scheduleExpire(key, time):
    r.expire(key,time)
