from django.contrib import auth
from django.contrib.auth import load_backend
from django.contrib.auth.backends import RemoteUserBackend
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.contrib.auth.middleware import AuthenticationMiddleware



def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = auth.get_user(request)
    return request._cached_user


class AuthenticateMiddleware(AuthenticationMiddleware):
    def process_request(self, request):
        if not hasattr(request, 'session'):
            raise ImproperlyConfigured(
                "The Django authentication middleware requires session "
                "middleware to be installed. Edit your MIDDLEWARE setting to "
                "insert "
                "'django.contrib.sessions.middleware.SessionMiddleware' before "
                "'django.contrib.auth.middleware.AuthenticationMiddleware'."
            )
        
        request.user = SimpleLazyObject(lambda: get_user(request))
        
        authentication_paths = ['/api/login', '/api/register', '/api/logout' ]
        if request.path in authentication_paths:
            return None

        # if request.user.is_authenticated():
        key_name = request.COOKIES.get('jwt')
        if key_name not in request.session:
            raise AuthenticationFailed('No token in Session, login Again')

        token = request.session[key_name]
        # print(request.path)
        # print(request.method)
        # print(request._get_scheme())
        # for x in request.session.keys():
        #     print(x)
        if not token: 
            print('no token from middleware')
            raise AuthenticationFailed('UnAuthenticated! Login Again!')
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            print('expired token middleware')
            raise AuthenticationFailed('UnAuthenticated! Session has been expired Login Again Please')