from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:character_name>", views.find_anime, name="find_anime"),
]
