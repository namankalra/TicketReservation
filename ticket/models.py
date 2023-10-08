from django.contrib.auth.models import User
from django.db import models

from .utils import TicketStatus


class Location(models.Model):
    name = models.CharField(max_length=100)
    lat = models.DecimalField(max_digits=22, decimal_places=16)
    long = models.DecimalField(max_digits=22, decimal_places=16)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Ticket(models.Model):
    unique_ticket_id = models.CharField(max_length=50, unique=True)
    source = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='source_tickets')
    destination = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='destination_tickets')
    travel_date = models.DateField()
    passenger_name = models.CharField(max_length=100)
    passenger_phone = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    seat_number = models.CharField(max_length=10)
    status = models.CharField(choices=TicketStatus.choices, max_length=30)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
