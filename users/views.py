from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
import jwt, datetime
import random
import uuid
import hashlib

from .TokenManager import setValue, getValue, checkForExistence
from rest_framework.parsers import JSONParser
 

ACCESS_AGE_MINUTES = 1
REFRESH_AGE_MINUTES = 3

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

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
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
        data = JSONParser().parse(request)
        password = data['password']
        if not password:
            return Response({ "message" : "Please enter your password"})
        
        data['password'] = hash_password(password)
        usermodel = User(name=data['name'], email=data['email'], password=data['password'])
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            final_data = serializer.data
            final_data['password'] = '*********************'
            return  Response(final_data)
        else:
            return Response({"error" : "not valid"})


class LoginView(APIView):

    def post(self, request):

        #authentication
        email  = request.data['email']
        password = request.data['password']
        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed('User not found')
        hashed_password = user.password
        if not check_password(hashed_password, password):
            raise AuthenticationFailed('Incorrest password')


        # token preparation
        secret_key = generateRandomKey()
        access_token = create_token(user.id, secret_key, ACCESS_AGE_MINUTES)
        refresh_token = create_token(user.id, secret_key, REFRESH_AGE_MINUTES)

        
        # key generation
        key_name = generateRandomKey()
        while checkForExistence(key_name + "_secret"):
            key_name = generateRandomKey()


        access_key = key_name + "_access"
        setValue(access_key, access_token, ACCESS_AGE_MINUTES*60)
        setValue(key_name + "_secret", secret_key, REFRESH_AGE_MINUTES*60)


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

class RefreshToken(APIView):
    def post(self, request):
        key_name = request.COOKIES.get('jwt')
        token = request.COOKIES.get('refresh')
        if not token:
            return Response({"Error" : "please login again!"})
        secret_key = getValue(key_name + "_secret")
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        access_token = create_token(payload['id'], secret_key, ACCESS_AGE_MINUTES)
        setValue(key_name + "_access", access_token, ACCESS_AGE_MINUTES*60)
        return Response({"message" : "successful"})
        



class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.delete_cookie('refresh')
        response.data = {
            "message" : 'success'
        }

        return response