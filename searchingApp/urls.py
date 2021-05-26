from django.urls import path
from .views import searchingView, topicRegistration, bulkRegistration


urlpatterns = [
    path('', searchingView.as_view()),
    path('register',topicRegistration.as_view()),
    path('bulk_register',bulkRegistration.as_view())
]

