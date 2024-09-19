from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices
from apps.listings.models import Listing
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class TestBookingDetailView(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(username='user', email='user@example.com', password='password')
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='password')
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')

        # Создаем листинг и бронирование
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.owner,
            description='A test description',
            location='Berlin',
            address='123 Test St',
            property_type=PropertyTypeChoices.OTHER,
            price=500000,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            status=BookingStatusChoices.PENDING
        )

        self.deleted_booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now() + timedelta(days=3),
            end_date=timezone.now() + timedelta(days=4),
            status=BookingStatusChoices.DELETED
        )

    def test_unauthenticated_user_access(self):
        url = reverse('booking-detail', kwargs={'id': self.booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_access_to_own_booking(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-detail', kwargs={'id': self.booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_owner_access_to_listing_booking(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('booking-detail', kwargs={'id': self.booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_access_to_booking(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('booking-detail', kwargs={'id': self.booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_no_access(self):
        other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='password')
        self.client.force_authenticate(user=other_user)
        url = reverse('booking-detail', kwargs={'id': self.booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_to_nonexistent_booking(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-detail', kwargs={'id': 9999})  # Несуществующий ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_access_deleted_booking(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-detail', kwargs={'id': self.deleted_booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_cannot_access_deleted_booking(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('booking-detail', kwargs={'id': self.deleted_booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_access_deleted_booking(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('booking-detail', kwargs={'id': self.deleted_booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
