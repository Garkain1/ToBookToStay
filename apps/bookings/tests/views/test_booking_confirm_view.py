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


class TestBookingConfirmView(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.listing_owner = User.objects.create_user(
            username='listing_owner',  # Добавляем username
            email='listing_owner@example.com',
            password='password123'
        )
        self.booking_owner = User.objects.create_user(
            username='booking_owner',  # Добавляем username
            email='booking_owner@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other_user',  # Добавляем username
            email='other_user@example.com',
            password='password123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin_user',  # Добавляем username
            email='admin@example.com',
            password='admin123'
        )

        # Создаем листинг и бронирование
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.listing_owner,
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

    def test_confirm_booking_unauthenticated_user(self):
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_confirm_booking_non_listing_owner(self):
        self.client.login(email='other_user@example.com', password='password123')
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_booking_by_owner(self):
        self.client.login(email='listing_owner@example.com', password='password123')
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatusChoices.CONFIRMED)

    def test_confirm_booking_invalid_status(self):
        self.booking.status = BookingStatusChoices.CANCELED
        self.booking.save()
        self.client.login(email='listing_owner@example.com', password='password123')
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, 'Booking can only be confirmed from the request status.', status_code=400)

    def test_confirm_booking_admin_user(self):
        self.client.login(email='admin@example.com', password='admin123')
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_booking_with_invalid_data(self):
        self.client.login(email='listing_owner@example.com', password='password123')
        url = reverse('booking-confirm', kwargs={'id': 9999})  # Несуществующее бронирование
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_confirm_booking_by_booking_owner(self):
        # Проверка, что владелец бронирования не может подтвердить его
        self.client.login(email='booking_owner@example.com', password='password123')
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_booking_status_transition(self):
        # Проверка статуса до и после подтверждения
        self.client.login(email='listing_owner@example.com', password='password123')
        self.assertEqual(self.booking.status, BookingStatusChoices.REQUEST)  # Статус до подтверждения
        url = reverse('booking-confirm', kwargs={'id': self.booking.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatusChoices.CONFIRMED)  # Статус после подтверждения
