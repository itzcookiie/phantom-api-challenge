from django.urls import path

from . import views

urlpatterns = [
    path("", views.get_anime, name="get_anime"),
    path("<str:character_name>", views.find_anime, name="find_anime"),
]
