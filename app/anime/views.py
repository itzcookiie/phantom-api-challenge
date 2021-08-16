import logging
from random import random

import requests
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from ratelimit.decorators import ratelimit

logger = logging.getLogger("mylogger")


class APIService:
    def __init__(self, url, params, error_message):
        self.url = url
        self.params = params
        self.cache = {}
        self.headers = {}
        self.response = None
        self.error_message = {"quote": error_message, "status": "Error"}

    def get(self):
        self.response = requests.get(
            self.url, headers=self.headers, params=self.params
        )

    def valid_response(self):
        return (
            self.response.status_code == requests.codes.ok
            or self.response.status_code == requests.codes.not_modified
        )

    def data_not_modified(self):
        return self.response.status_code == requests.codes.not_modified

    def updateCache(self, **kwargs):
        self.__updateHeaders(**kwargs)

    def __updateHeaders(self, **headers):
        self.headers.update(**headers)


@ratelimit(key="ip", rate="100/h")
def get_anime(request):
    params = {
        "q": "",
        "order_by": "members",
        "sort": "desc",
        "limit": 10,
        "page": "1",
    }
    url = "https://api.jikan.moe/v3/search/anime"
    anime_api = APIService(url, params, "Could not find any anime")

    if cache.get("index"):
        headers = {"If-None-Match": cache.get("index").get("e_tag")}
        anime_api.updateCache(**headers)
        anime_api.get()
    else:
        anime_api.get()
        cache.set(
            "index",
            {
                "data": anime_api.response.json(),
                "e_tag": anime_api.response.headers.get("ETag"),
            },
        )

    if anime_api.valid_response():
        user_response = (
            cache.get("index").get("data")
            if anime_api.data_not_modified()
            else anime_api.response.json()
        )
    else:
        user_response = anime_api.error_message

    return JsonResponse(user_response)


@ratelimit(key="ip", rate="100/h")
def find_anime(request, character_name):
    quote_api = APIService(
        "https://animechan.vercel.app/api/quotes/character",
        {"name": character_name},
        f"Could not find any quotes for {character_name}",
    )
    quote_api.get()
    if quote_api.valid_response():
        anime_name = quote_api.response.json().pop(0)["anime"]
        anime_api = APIService(
            "https://api.jikan.moe/v3/search/anime",
            {"q": anime_name},
            f"Could not find any anime for {anime_name}",
        )
        if cache.get("find_anime_e_tag"):
            headers = {"If-None-Match": cache.get("find_anime_e_tag")}
            anime_api.updateCache(**headers)
            anime_api.get()
        else:
            anime_api.get()
            cache.set(
                "find_anime_e_tag", anime_api.response.headers.get("ETag")
            )

        if anime_api.valid_response():
            return JsonResponse(anime_api.response.json())
        else:
            return JsonResponse(anime_api.error_message)
    else:
        return JsonResponse(quote_api.error_message)
