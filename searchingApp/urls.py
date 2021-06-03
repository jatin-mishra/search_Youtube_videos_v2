from django.urls import path
from .views import searchingView, topicRegistration, bulkRegistration, videosWithDateFilter,textSearch


urlpatterns = [
    path('', searchingView.as_view()),
    path('register',topicRegistration.as_view()),
    path('bulk_register',bulkRegistration.as_view()),
    path('_filter',videosWithDateFilter.as_view()),
    path('_textsearch',textSearch.as_view())
]

