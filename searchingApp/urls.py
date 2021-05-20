from django.urls import path
from .views import searchingView, searchingDefaultView


urlpatterns = [
    path('<int:n>', searchingView.as_view()),
    path('', searchingDefaultView.as_view()),
]

