from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from rest_framework import status
import jwt, datetime
import random
import uuid
import hashlib

from .TokenManager import setValue, getValue, checkForExistence, scheduleExpire
from pymodm.errors import DoesNotExist
 

ACCESS_AGE_MINUTES = 30
REFRESH_AGE_MINUTES = 120

def generateRandomKey(fixed_length=10):
    allowedchars = 'abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()'
    startIndex = 0
    lastIndex = len(allowedchars)-1
    random_key = ''
    for _ in range(fixed_length):
        random_key = random_key + allowedchars[random.randint(startIndex, lastIndex)]
    return random_key


def create_token(user_id, secret_key, age_limit, algorithm='HS256'):
    payload = {
        'id' : user_id,
        'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=age_limit),
        'iat' : datetime.datetime.utcnow()
    }

    try:
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
    except jwt.ExpiredSignatureError:
        return AuthenticationFailed("Try again!! cann't create token")

    return token


# Create your views here.
def hash_password(password):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
    
def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


class RegisterView(APIView):
    def post(self, request):
        data = request.data
        password = data.get('password')
        name = data.get('name')
        email = data.get('email')

        if password and  email and name:
            if password.isspace() or name.isspace() or email.isspace():
                return Response({"mesage" : "There must be some value for name,email,password"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            data['password'] = hash_password(password)

            # check if user is already present or not
            try:
                User.objects.raw({"_id" : email}).first()
                return Response({"message" : "user already registered"},status=status.HTTP_406_NOT_ACCEPTABLE)
            except DoesNotExist:
                usermodel = User(name=data['name'], email=data['email'], password=data['password'])
                usermodel.save()
                final_data = usermodel.serialize()
                final_data['password'] = '*********************'
                return  Response(final_data)

        return Response({ "message" : "Missing Values, check username, password or email!! "}, status=status.HTTP_406_NOT_ACCEPTABLE)
        


class LoginView(APIView):

    def post(self, request):

        #authentication
        email  = request.data.get('email')
        password = request.data.get('password')

        if email and password:
            # user = User.objects.filter(email=email).first()
            try:
                user = User.objects.raw({"_id": email}).first()
            except DoesNotExist:
                return Response({ "message" : "user does not exist"}, status=status.HTTP_401_UNAUTHORIZED)
                            
                
            hashed_password = user.password
            if not check_password(hashed_password, password):
                return Response({ "message" : "Wrong Password"}, status=status.HTTP_401_UNAUTHORIZED)



            # token preparation
            secret_key = generateRandomKey()
            access_token = create_token(user.email, secret_key, ACCESS_AGE_MINUTES)
            refresh_token = create_token(user.email, secret_key, REFRESH_AGE_MINUTES)

            
            # key generation
            key_name = generateRandomKey()
            while checkForExistence(key_name + "_secret"):
                key_name = generateRandomKey()


            # adding access token and secret key into redis
            access_key = key_name + "_access"
            setValue(access_key, access_token, ACCESS_AGE_MINUTES*60)
            setValue(key_name + "_secret", secret_key, REFRESH_AGE_MINUTES*60)

            # expiry for refreshtoken cookie
            expiry = datetime.datetime.strftime( datetime.datetime.utcnow() + datetime.timedelta(minutes=REFRESH_AGE_MINUTES) ,"%a, %d-%b-%Y %H:%M:%S GMT")


            # save randomkey on cookie
            response = Response()
            response.set_cookie(key='jwt',value=key_name, httponly=True)
            response.set_cookie(key='refresh',value=refresh_token, httponly=True, expires = expiry )
            
            response.data = {
                'jwt' : key_name,
                'refresh' : refresh_token
            }
            return response
        return Response({"message" : 'User or password is not found'}, status=status.HTTP_401_UNAUTHORIZED)


class RefreshToken(APIView):
    def post(self, request):
        key_name = request.COOKIES.get('jwt')
        token = request.COOKIES.get('refresh')
        if not token:
            return Response({"Error" : "please login again!"},status=status.HTTP_401_UNAUTHORIZED)

        if not key_name:
            return Response({"message" : "no jwt token"}, status=status.HTTP_401_UNAUTHORIZED)

        secret_key = getValue(key_name + "_secret")
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('UnAuthenticated! Session has been expired Login Again Please') 

        access_token = create_token(payload['id'], secret_key, ACCESS_AGE_MINUTES)
        setValue(key_name + "_access", access_token, ACCESS_AGE_MINUTES*60)
        return Response({"message" : "successful"}, status=status.HTTP_201_CREATED)
        



class LogoutView(APIView):
    def post(self, request):
        response = Response()
        key_name = request.COOKIES.get('jwt')

        scheduleExpire(key_name + "_secret",0)
        scheduleExpire(key_name + "_access",0)

        response.delete_cookie('jwt')
        response.delete_cookie('refresh')
        response.data = {
            "message" : 'success'
        }

        return response