import re

from django.db import models
from django.utils.translation import gettext_lazy as _


# We should store these constants in the environment file
JWT_SECRET = "109BC922ADEC40AA9D6BFEB6F1EBF9A1"


class TicketStatus(models.TextChoices):
    PENDING = 'Pending', _('Pending')
    CONFIRMED = 'Confirmed', _('Confirmed')
    CANCELLED = 'Cancelled', _('Cancelled')


def is_valid_mobile(mobile):
    """
        Function to check whether the mobile no is valid or not.

        This method takes a mobile no and returns boolean value based on a regex expression.
    """
    regex = re.compile(r'^[6-9]\d{9}$')
    return re.fullmatch(regex, mobile)


def calculate_price(source, destination):
    """
        Function to calculate price between the source and destination.

        This method takes source and destination and returns price of travelling in car based on distance and price per km.
    """
    base_fare = 50
    price_per_km = 7

    lat1, lon1 = source.lat, source.long
    lat2, lon2 = destination.lat, destination.long
    distance = abs(lat1 - lat2) + abs(lon1 - lon2)

    price = base_fare + (distance * price_per_km)

    return price
