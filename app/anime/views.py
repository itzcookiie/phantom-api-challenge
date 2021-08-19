import logging

import requests
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from ratelimit.decorators import ratelimit

logger = logging.getLogger("mylogger")


class APIService:
    def __init__(self):
        self.url = None
        self.params = None
        self.headers = {}
        self.response = None
        self.error_message = {"quote": None, "status": "Error"}

    def get(self):
        self.response = requests.get(
            self.url, headers=self.headers, params=self.params
        )

    def valid_response(self):
        return self.response.status_code == requests.codes.ok

    def data_not_modified(self):
        return self.response.status_code == requests.codes.not_modified

    def updateFields(self, **kwargs):
        for field in kwargs:
            if field in vars(self):
                if field == "error_message":
                    self[field]["quote"] = kwargs[field]
                else:
                    self[field] = kwargs[field]

    def updateCache(self, **kwargs):
        self.__updateHeaders(**kwargs)

    def __updateHeaders(self, **headers):
        self.headers.update(**headers)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


anime_api = APIService()
quote_api = APIService()


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
    anime_api.updateFields(
        url=url, params=params, error_message="Could not find any anime"
    )

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

    if anime_api.data_not_modified():
        return JsonResponse(cache.get("index").get("data"))
    elif anime_api.valid_response():
        return JsonResponse(anime_api.response.json())
    else:
        return JsonResponse(anime_api.error_message)


@ratelimit(key="ip", rate="100/h")
def find_anime(request, character_name):
    quote_api.updateFields(
        url="https://animechan.vercel.app/api/quotes/character",
        params={"name": character_name},
        error_message=f"Could not find any quotes for {character_name}",
    )
    quote_api.get()
    if quote_api.valid_response():
        anime_name = quote_api.response.json().pop(0)["anime"]
        anime_api.updateFields(
            url="https://api.jikan.moe/v3/search/anime",
            params={"q": anime_name},
            error_message=f"Could not find any anime for {anime_name}",
        )
        if cache.get("find_anime"):
            headers = {"If-None-Match": cache.get("find_anime").get("e_tag")}
            anime_api.updateCache(**headers)
            anime_api.get()
        else:
            anime_api.get()
            cache.set(
                "find_anime",
                {
                    "data": anime_api.response.json(),
                    "e_tag": anime_api.response.headers.get("ETag"),
                },
            )

        if anime_api.data_not_modified():
            return JsonResponse(cache.get("find_anime").get("data"))
        if anime_api.valid_response():
            return JsonResponse(anime_api.response.json())
        else:
            return JsonResponse(anime_api.error_message)
    else:
        return JsonResponse(quote_api.error_message)
