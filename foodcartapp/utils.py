import requests

from django.conf import settings
from requests.exceptions import HTTPError, RequestException
from collections import defaultdict
from geopy import distance

from .models import RestaurantMenuItem


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
    from geo.models import AddressPoint
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


def get_available_restaurants_for_orders(orders):
    menu_items = (
        RestaurantMenuItem.objects
        .filter(availability=True)
        .select_related('restaurant', 'product')
    )

    restaurant_menu = defaultdict(set)
    for item in menu_items:
        restaurant_menu[item.restaurant].add(item.product_id)

    for order in orders:
        order_products = set(order.products.values_list('product_id', flat=True))
        available_restaurants = []

        for restaurant, products in restaurant_menu.items():
            if order_products.issubset(products):
                distance = get_distance(order, restaurant)
                try:
                    distance = float(str(distance).split()[0])
                except (TypeError, ValueError, AttributeError):
                    distance = None
                available_restaurants.append((restaurant, distance))

        order.available_restaurants = sorted(
            available_restaurants,
            key=lambda x: x[1] if x[1] is not None else 9999
        )

    return orders
