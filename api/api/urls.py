from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("anime/", include("anime.urls")),
    path("admin/", admin.site.urls),
]
