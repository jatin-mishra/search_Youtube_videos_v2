from django.urls import path
from .views import searchingView, topicRegistration


urlpatterns = [
    path('', searchingView.as_view()),
    path('register',topicRegistration.as_view())
]

