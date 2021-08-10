from random import random

import requests
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from ratelimit.decorators import ratelimit


@ratelimit(key="ip", rate="100/h")
def index(request):
    payload = {
        "q": "",
        "order_by": "members",
        "sort": "desc",
        "limit": 10,
        "page": "1",
    }
    url = "https://api.jikan.moe/v3/search/anime"
    if cache.get("index_e_tag"):
        headers = {"If-None-Match": cache.get("index_e_tag")}
        response = requests.get(url, headers=headers, params=payload)
    else:
        response = requests.get(url, params=payload)
        cache.set("index_e_tag", response.headers.get("ETag"))
    return JsonResponse(response.json())


@ratelimit(key="ip", rate="100/h")
def find_anime(request, character_name):
    quote_api_payload = {"name": character_name}
    quote_api_response = requests.get(
        "https://animechan.vercel.app/api/quotes/character",
        params=quote_api_payload,
    )
    if (
        quote_api_response.status_code == requests.codes.ok
        or quote_api_response.status_code
        == requests.codes.get("If-None-Match")
    ):
        # TODO Make sure json contains correct content and not error message
        quote_api_json = quote_api_response.json()
        anime_name = quote_api_json.pop(0)["anime"]
        anime_api_payload = {"q": anime_name}
        anime_api_url = "https://api.jikan.moe/v3/search/anime"
        if cache.get("find_anime_e_tag"):
            headers = {"If-None-Match": cache.get("find_anime_e_tag")}
            anime_api_response = requests.get(
                anime_api_url, headers=headers, params=anime_api_payload
            )
        else:
            anime_api_response = requests.get(
                anime_api_url, params=anime_api_payload
            )
            cache.set(
                "find_anime_e_tag", anime_api_response.headers.get("ETag")
            )

        if (
            anime_api_response.status_code == requests.codes.ok
            or anime_api_response.status_code
            == requests.codes.get("If-None-Match")
        ):
            # TODO Make sure json contains correct content and not error message
            return JsonResponse(anime_api_response.json())
        else:
            return JsonResponse(
                {
                    "quote": f"Could not find any anime for {anime_name}",
                    "status": "Error",
                }
            )
    else:
        return JsonResponse(
            {
                "quote": f"Could not find any quotes for {character_name}",
                "status": "Error",
            }
        )
