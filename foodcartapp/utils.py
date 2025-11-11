import requests

from django.conf import settings
from requests.exceptions import HTTPError, RequestException

from geopy import distance


def fetch_coordinates(address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {
        "geocode": address,
        "apikey": settings.YANDEX_API_KEY,
        "format": "json"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection'][
            'featureMember']
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lat, lon
    except (HTTPError, KeyError, ValueError, RequestException):
        return None


def get_address_point(address):
    from .models import AddressPoint
    address_point, created = AddressPoint.objects.get_or_create(
        address=address
    )
    if created:
        lat, lon = fetch_coordinates(address)
        address_point.latitude = lat
        address_point.longitude = lon
        address_point.save()

    return address_point.latitude, address_point.longitude


def get_distance(order, restaurant):
    order_point = get_address_point(order.address)
    restaurant_point = get_address_point(restaurant.address)
    distance_between = distance.distance(order_point, restaurant_point).km
    return f'{distance_between:.3f} км'
