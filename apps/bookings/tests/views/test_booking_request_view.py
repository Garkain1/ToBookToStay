from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.models import Listing
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class TestBookingRequestView(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.booking_owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other_user', email='other@example.com', password='password123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='admin123'
        )

        # Создаем листинг и бронирование
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.other_user,  # Владелец листинга - другой пользователь
            description='Test description',
            location='Test City',
            address='123 Test St',
            property_type=PropertyTypeChoices.HOUSE,
            price=500000,
            rooms=3,
            status = ListingStatusChoices.ACTIVE
        )

        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.booking_owner,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=7),
            status=BookingStatusChoices.PENDING
        )

    def test_request_booking_unauthenticated_user(self):
        url = reverse('booking-request', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_request_booking_non_owner_user(self):
        self.client.login(email='other@example.com', password='password123')
        url = reverse('booking-request', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_request_booking_by_owner(self):
        self.client.login(email='owner@example.com', password='password123')
        url = reverse('booking-request', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatusChoices.REQUEST)

    def test_request_booking_from_invalid_status(self):
        self.booking.status = BookingStatusChoices.CONFIRMED
        self.booking.save()
        self.client.login(email='owner@example.com', password='password123')
        url = reverse('booking-request', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_booking_admin_user(self):
        self.client.login(email='admin@example.com', password='admin123')
        url = reverse('booking-request', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_booking_with_invalid_data(self):
        self.client.login(email='owner@example.com', password='password123')
        url = reverse('booking-request', kwargs={'id': 9999})  # Несуществующее бронирование
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
