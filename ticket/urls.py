from django.urls import path
from .views import register, login, locations, tickets, view_ticket, cancel_ticket

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('locations/', locations, name='locations'),
    path('tickets/', tickets, name='tickets'),
    path('view_ticket/<str:token>', view_ticket, name='view_ticket'),
    path('cancel_ticket/<str:token>', cancel_ticket, name='cancel_ticket')
]