from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("anime/", include("anime.urls")),
    path("admin/", admin.site.urls),
    path(
        "<path:resource>",
        TemplateView.as_view(template_name="anime/index.html"),
    ),
]
