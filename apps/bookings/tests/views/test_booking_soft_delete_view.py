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


class TestBookingSoftDeleteView(APITestCase):
    def setUp(self):
        # Создание пользователей
        self.listing_owner = User.objects.create_user(username='listing_owner', email='listing_owner@example.com', password='password123')
        self.booking_owner = User.objects.create_user(username='booking_owner', email='booking_owner@example.com', password='password123')
        self.other_user = User.objects.create_user(username='other_user', email='other_user@example.com', password='password123')
        self.admin_user = User.objects.create_superuser(username='admin_user', email='admin@example.com', password='admin123')

        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.listing_owner,  # Владелец листинга - другой пользователь
            description='Test description',
            location='Test City',
            address='123 Test St',
            property_type=PropertyTypeChoices.HOUSE,
            price=500000,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.booking_owner,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
            status=BookingStatusChoices.REQUEST
        )

    def test_soft_delete_booking_unauthenticated_user(self):
        url = reverse('booking-soft-delete', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_soft_delete_booking_non_admin_user(self):
        self.client.login(email='listing_owner@example.com', password='password123')
        url = reverse('booking-soft-delete', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_booking_by_admin_user(self):
        self.client.login(email='admin@example.com', password='admin123')
        url = reverse('booking-soft-delete', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatusChoices.DELETED)

    def test_soft_delete_booking_with_invalid_data(self):
        self.client.login(email='admin@example.com', password='admin123')
        url = reverse('booking-soft-delete', kwargs={'id': 9999})  # Несуществующее бронирование
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_soft_delete_booking_status_transition(self):
        self.client.login(email='admin@example.com', password='admin123')
        self.assertEqual(self.booking.status, BookingStatusChoices.REQUEST)
        url = reverse('booking-soft-delete', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatusChoices.DELETED)