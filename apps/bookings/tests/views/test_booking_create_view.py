from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class TestBookingCreateView(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Создаем пользователей
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='password'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
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
            owner=self.user,
            description='A beautiful listing',
            location='Test Location',
            address='123 Test St',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.0,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

    def _get_dates(self, start_offset, end_offset):
        start_date = (timezone.now() + timedelta(days=start_offset)).date().isoformat()
        end_date = (timezone.now() + timedelta(days=end_offset)).date().isoformat()
        return start_date, end_date

    def test_create_booking_unauthenticated(self):
        url = reverse('booking-create', kwargs={'listing_id': self.listing.id})
        start_date, end_date = self._get_dates(10, 12)
        data = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 401)  # Незарегистрированный пользователь

    def test_create_booking_authenticated_user(self):
        self.client.login(email='user@example.com', password='password')
        url = reverse('booking-create', kwargs={'listing_id': self.listing.id})
        start_date, end_date = self._get_dates(10, 12)
        data = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)  # Ожидаем успешное создание
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.user, self.user)  # Проверка пользователя

    def test_create_booking_admin_with_user_field(self):
        self.client.login(email='admin@example.com', password='password')
        url = reverse('booking-create', kwargs={'listing_id': self.listing.id})
        start_date, end_date = self._get_dates(10, 12)
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'user': self.other_user.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)  # Ожидаем успешное создание
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.user, self.other_user)  # Проверка пользователя, назначенного админом

    def test_create_booking_invalid_user_as_non_admin(self):
        self.client.login(email='user@example.com', password='password')
        url = reverse('booking-create', kwargs={'listing_id': self.listing.id})
        start_date, end_date = self._get_dates(10, 12)
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'user': self.other_user.id  # Попытка указать другого пользователя
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)  # Ожидаем успешное создание
        booking = Booking.objects.first()
        # Проверка, что установился текущий пользователь, а не указанный
        self.assertEqual(booking.user, self.user)

    def test_create_booking_admin_invalid_user(self):
        self.client.login(email='admin@example.com', password='password')
        url = reverse('booking-create', kwargs={'listing_id': self.listing.id})
        start_date, end_date = self._get_dates(10, 12)
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'user': 999  # Несуществующий пользователь
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)  # Ошибка валидации
        self.assertIn('user', response.data)
