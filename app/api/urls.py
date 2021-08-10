from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView

favicon_view = RedirectView.as_view(url="/static/favicon.ico", permanent=True)

urlpatterns = [
    path("anime/", include("anime.urls")),
    re_path(r"^favicon\.ico$", favicon_view),
    path("admin/", admin.site.urls),
]
