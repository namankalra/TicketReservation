import jwt
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Location, Ticket
from .serializers import RegistrationSerializer, LoginSerializer, LocationSerializer, TicketSerializer
from uuid import uuid4

from .utils import calculate_price_car, calculate_price_flight, calculate_price_train, TicketStatus, JWT_SECRET, \
    is_valid_mobile, TravelModes
from datetime import datetime


@api_view(['POST'])
def register(request):
    """
        Create a new User object.

        This method creates a new User object.
        It expects username, password, email, first_name, last_name and the response will indicate the success or failure of the operation.
    """
    if request.method == 'POST':
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('email') and User.objects.filter(
                    email=serializer.validated_data.get('email')).exists():
                return Response({'message': 'User already exists with this email'},
                                status=status.HTTP_409_CONFLICT)

            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'user_id': user.id, 'token': token.key, 'message': 'User registered successfully'},
                            status=status.HTTP_201_CREATED)
        return Response({'message': 'Registration failed', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    """
        Login a User through username and password.

        This method allows a User to login into the system based on the user credentials.
    """
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                if user.password == password and user.is_active:
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({'user_id': user.id, 'token': token.key, 'message': 'Login successful'},
                                    status=status.HTTP_200_OK)
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'message': 'Login failed', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def locations(request):
    """
        Create a new Location object & Fetch Location Details based on request method.

        This method creates a new Location object if request method is POST.
        It expects name, latitude, longitude and the response will indicate the success or failure of the operation.

        This method fetch Location objects if request method is GET.
    """
    if request.method == 'POST':
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            if Location.objects.filter(name=serializer.validated_data.get('name')).exists():
                return Response({'message': 'Location already exists'},
                                status=status.HTTP_409_CONFLICT)

            location = serializer.save(created_by=request.user)
            return Response({'location_id': location.id, 'message': 'Location created successfully'},
                            status=status.HTTP_201_CREATED)
        return Response({'message': 'Location creation failed', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        return Response({'data': serializer.data, 'message': 'Locations fetched successfully'},
                        status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def tickets(request):
    """
        Create a new Ticket object & Fetch Ticket Details based on request method.

        This method creates a new Ticket object if request method is POST.
        It expects source, destination, travel_date, passenger_name, passenger_phone, seat_number and the response will indicate the success or failure of the operation.

        This method fetch Ticket objects if request method is GET.
        It can be used to view all objects or filter them based on query parameters.
    """
    if request.method == 'POST':
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            if not is_valid_mobile(serializer.validated_data.get('passenger_phone')):
                return Response({'message': 'Invalid passenger mobile no'},
                                status=status.HTTP_400_BAD_REQUEST)
            if serializer.validated_data.get('source') == serializer.validated_data.get('destination'):
                return Response({'message': 'Source & Destination cannot be same'},
                                status=status.HTTP_409_CONFLICT)
            if Ticket.objects.filter(source=serializer.validated_data.get('source'),
                                     destination=serializer.validated_data.get('destination'),
                                     travel_date=serializer.validated_data.get('travel_date'),
                                     travel_mode=serializer.validated_data.get('travel_mode'),
                                     seat_number=serializer.validated_data.get('seat_number'),
                                     status=TicketStatus.CONFIRMED).exists():
                return Response({'message': 'Seat already booked'}, status=status.HTTP_400_BAD_REQUEST)

            price = 0
            if serializer.validated_data.get('travel_mode') == TravelModes.CAR:
                price = calculate_price_car(serializer.validated_data['source'],
                                            serializer.validated_data['destination'])
            elif serializer.validated_data.get('travel_mode') == TravelModes.FLIGHT:
                price = calculate_price_flight(serializer.validated_data['source'],
                                               serializer.validated_data['destination'])
            elif serializer.validated_data.get('travel_mode') == TravelModes.TRAIN:
                price = calculate_price_train(serializer.validated_data['source'],
                                              serializer.validated_data['destination'])

            ticket = serializer.save(unique_ticket_id='TID-'+str(uuid4()),
                                     price=price, status=TicketStatus.CONFIRMED,
                                     created_by=request.user)

            # View & Cancel Ticket Url should be sent to the passenger phone via text message
            # These urls can further be short using any URL Shortener
            passenger_ticket_token = jwt.encode({'unique_ticket_id': ticket.unique_ticket_id},
                                                JWT_SECRET, algorithm="HS256")
            view_ticket_url = request.build_absolute_uri(reverse('view_ticket',
                                                                 kwargs={'token': passenger_ticket_token}))
            cancel_ticket_url = request.build_absolute_uri(reverse('cancel_ticket',
                                                                   kwargs={'token': passenger_ticket_token}))
            return Response({'ticket_id': ticket.id, 'passenger_view_ticket_url': view_ticket_url,
                             'passenger_cancel_ticket_url': cancel_ticket_url,
                             'message': 'Ticket created successfully'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Ticket creation failed', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        filter_dict = {}
        if request.query_params.get('source'):
            filter_dict['source'] = request.query_params.get('source')
        if request.query_params.get('destination'):
            filter_dict['destination'] = request.query_params.get('destination')
        if request.query_params.get('travel_date_from'):
            filter_dict['travel_date__gte'] = datetime.strptime(request.query_params.get('travel_date_from'),
                                                                '%Y-%m-%d').date()
        if request.query_params.get('travel_date_to'):
            filter_dict['travel_date__lte'] = datetime.strptime(request.query_params.get('travel_date_to'),
                                                                '%Y-%m-%d').date()
        if request.query_params.get('passenger_name'):
            filter_dict['passenger_name'] = request.query_params.get('passenger_name')

        tickets = Ticket.objects.filter(**filter_dict)
        serializer = TicketSerializer(tickets, many=True)
        return Response({'data': serializer.data, 'message': 'Tickets fetched successfully'},
                        status=status.HTTP_200_OK)


@api_view(['GET'])
def view_ticket(request, token):
    """
        Retrieve a Ticket object in order to view ticket by the passenger.

        This method retrieves a Ticket object from the database through jwt token.
    """
    if request.method == 'GET':
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms="HS256")
            unique_ticket_id = data.get('unique_ticket_id')
        except Exception as e:
            return Response({'message': 'Unable to fetch token data'}, status=status.HTTP_400_BAD_REQUEST)

        if not Ticket.objects.filter(unique_ticket_id=unique_ticket_id).exists():
            return Response({'message': 'Invalid ticket id'}, status=status.HTTP_404_NOT_FOUND)

        ticket = Ticket.objects.get(unique_ticket_id=unique_ticket_id)
        serializer = TicketSerializer(ticket)
        return Response({'data': serializer.data, 'message': 'Ticket fetched successfully'},
                        status=status.HTTP_200_OK)


@api_view(['PUT'])
def cancel_ticket(request, token):
    """
        Update a Ticket object.

        This method updates an existing Ticket object.
        It helps the passenger to cancel ticket based in jwt token, and the response will indicate the success or failure of the operation.
    """
    if request.method == 'PUT':
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms="HS256")
            unique_ticket_id = data.get('unique_ticket_id')
        except Exception as e:
            return Response({'message': 'Unable to fetch token data'}, status=status.HTTP_400_BAD_REQUEST)

        if not Ticket.objects.filter(unique_ticket_id=unique_ticket_id).exists():
            return Response({'message': 'Invalid ticket id'}, status=status.HTTP_404_NOT_FOUND)

        ticket = Ticket.objects.get(unique_ticket_id=unique_ticket_id)
        if ticket.status == TicketStatus.CONFIRMED:
            ticket.status = TicketStatus.CANCELLED
            ticket.save()
            return Response({'message': 'Ticket cancelled successfully'}, status=status.HTTP_200_OK)
        elif ticket.status == TicketStatus.CANCELLED:
            return Response({'message': 'Ticket already cancelled'}, status=status.HTTP_200_OK)
        return Response({'message': 'Ticket cancellation failed'}, status=status.HTTP_400_BAD_REQUEST)
