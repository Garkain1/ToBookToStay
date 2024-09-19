from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.models import Listing
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class TestBookingUpdateView(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='password'
        )
        self.other_user = User.objects.create_user(
            email='other_user@example.com',
            username='otheruser',
            password='password'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='password'
        )

        # Создаем листинг
        self.listing = Listing.objects.create(
            title='Test Listing',
            description='Description',
            location='Berlin',
            address='Address',
            property_type=PropertyTypeChoices.HOUSE,
            price=500000,
            rooms=3,
            owner=self.user,
            status=ListingStatusChoices.ACTIVE
        )

        # Создаем бронирование
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=5)).date(),
            status=BookingStatusChoices.CONFIRMED
        )

        self.url = reverse('booking-update', kwargs={'id': self.booking.id})

    def test_update_booking_unauthenticated_user(self):
        response = self.client.put(self.url, {'start_date': timezone.now().date()})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_booking_other_user(self):
        self.client.login(email='other_user@example.com', password='password')
        response = self.client.patch(self.url, {'start_date': (timezone.now() + timedelta(days=1)).date()})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_booking_owner(self):
        self.client.login(email='user@example.com', password='password')
        response = self.client.patch(self.url, {'start_date': (timezone.now() + timedelta(days=1)).date()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.start_date, (timezone.now() + timedelta(days=1)).date())

    def test_update_booking_admin(self):
        self.client.login(email='admin@example.com', password='password')
        response = self.client.patch(self.url, {'start_date': (timezone.now() + timedelta(days=1)).date()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.start_date, (timezone.now() + timedelta(days=1)).date())

    def test_update_deleted_booking_by_non_admin(self):
        # Устанавливаем статус бронирования как DELETED
        self.booking.status = BookingStatusChoices.DELETED
        self.booking.save()

        # Логинимся как обычный пользователь
        self.client.login(email='user@example.com', password='password')

        # Пытаемся обновить удаленное бронирование
        response = self.client.patch(self.url, {'start_date': (timezone.now() + timedelta(days=1)).date()})

        # Проверяем, что запрос возвращает ошибку
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, "Cannot update a deleted booking.", status_code=400)

    def test_update_deleted_booking_by_admin(self):
        # Устанавливаем статус бронирования как DELETED
        self.booking.status = BookingStatusChoices.DELETED
        self.booking.save()

        # Логинимся как администратор
        self.client.login(email='admin@example.com', password='password')

        # Пытаемся обновить удаленное бронирование
        response = self.client.patch(self.url, {'start_date': (timezone.now() + timedelta(days=1)).date()})

        # Проверяем, что запрос возвращает ошибку
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, "Cannot update a deleted booking.", status_code=400)

    def test_partial_update_vs_full_update(self):
        self.client.login(email='user@example.com', password='password')

        # Частичное обновление
        response = self.client.patch(self.url, {'end_date': (timezone.now() + timedelta(days=7)).date()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.end_date, (timezone.now() + timedelta(days=7)).date())

        # Полное обновление (требует всех полей)
        response = self.client.put(self.url, {
            'start_date': (timezone.now() + timedelta(days=3)).date(),
            'end_date': (timezone.now() + timedelta(days=10)).date(),
            'listing': self.listing.id,
            'user': self.user.id,
            'status': BookingStatusChoices.CONFIRMED
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.start_date, (timezone.now() + timedelta(days=3)).date())
        self.assertEqual(self.booking.end_date, (timezone.now() + timedelta(days=10)).date())

    def test_update_booking_invalid_data(self):
        self.client.login(email='user@example.com', password='password')
        response = self.client.patch(self.url, {'start_date': 'invalid-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
