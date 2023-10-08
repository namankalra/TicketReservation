import math
import re

from django.db import models
from django.utils.translation import gettext_lazy as _


# We should store these constants in the environment file
JWT_SECRET = "109BC922ADEC40AA9D6BFEB6F1EBF9A1"


class TicketStatus(models.TextChoices):
    PENDING = 'Pending', _('Pending')
    CONFIRMED = 'Confirmed', _('Confirmed')
    CANCELLED = 'Cancelled', _('Cancelled')


class TravelModes(models.TextChoices):
    CAR = 'Car', _('Car')
    FLIGHT = 'Flight', _('Flight')
    TRAIN = 'Train', _('Train')


def is_valid_mobile(mobile):
    """
        Function to check whether the mobile no is valid or not.

        This method takes a mobile no and returns boolean value based on a regex expression.
    """
    regex = re.compile(r'^[6-9]\d{9}$')
    return re.fullmatch(regex, mobile)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
        Function to calculate distance between the source and destination.

        This method takes latitude and longitude of source and destination and returns distance based on Haversine formula.
    """
    # Radius of the Earth in kilometers
    earth_radius = 6371.0

    # Converting latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c
    return distance


def calculate_price_car(source, destination):
    """
        Function to calculate price between the source and destination.

        This method takes source and destination and returns price of travelling in car based on distance and price per km.
    """
    base_fare = 50
    price_per_km = 7
    distance = calculate_distance(source.lat, source.long, destination.lat, destination.long)
    price = base_fare + (distance * price_per_km)
    return price


def calculate_price_flight(source, destination):
    """
        Function to calculate price between the source and destination.

        This method takes source and destination and returns price of travelling in flight(economy) based on distance and price per km.
    """
    base_fare = 1000
    price_per_km = 5
    distance = calculate_distance(source.lat, source.long, destination.lat, destination.long)
    price = base_fare + (distance * price_per_km)
    return price


def calculate_price_train(source, destination):
    """
        Function to calculate price between the source and destination.

        This method takes source and destination and returns price of travelling in train(3rd AC class) based on distance and price per km.
    """
    base_fare = 300
    price_per_km = 3
    distance = calculate_distance(source.lat, source.long, destination.lat, destination.long)
    price = base_fare + (distance * price_per_km)
    return price
