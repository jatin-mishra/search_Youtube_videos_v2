from django.urls import path
from .views import searchingView


urlpatterns = [
    path('<int:n>', searchingView.as_view()),
]

