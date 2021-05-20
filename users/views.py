from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
import jwt, datetime
import random
# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return  Response(serializer.data)


class LoginView(APIView):



    def generateRandomKey(self, fixed_length=10):
        allowedchars = 'abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()'
        startIndex = 0
        lastIndex = len(allowedchars)-1
        random_key = ''
        for _ in range(fixed_length):
            random_key = random_key + allowedchars[random.randint(startIndex, lastIndex)]
        return random_key





    def post(self, request):
        email  = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrest password')

        payload = {
            'id' : user.id,
            'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat' : datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')
        
        # return token via cookies
        response = Response()

        # generaate a random key that is not present in session
        key_name = self.generateRandomKey()
        while key_name in request.session :
            key_name = self.generateRandomKey()

        # store key=randomkey, value=token
        request.session[key_name] = token

        # save randomkey on cookie
        response.set_cookie(key='jwt',value=key_name, httponly=True)
        response.data = {
            'jwt' : key_name
        }
        return response

class UserView(LoginRequiredMixin,APIView):
    def get(self, request):
        key_name = request.COOKIES.get('jwt')

        if key_name not in request.session:
            raise AuthenticationFailed('UnAuthenticated!')

        if not token:
            raise AuthenticationFailed('UnAuthenticated!')

        try:
            token = request.session[key_name]
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('UnAuthenticated')

        user = User.objects.filter(id=payload['id']).first() 

        return Response(UserSerializer(user).data)

class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            "message" : 'success'
        }

        return response