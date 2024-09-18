from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.bookings.serializers import BookingCreateSerializer
from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock


class TestBookingCreateSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.listing_owner = get_user_model().objects.create_user(
            username='listingowner',
            email='listingowner@example.com',
            password='password123'
        )
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.listing_owner,
            description='Test description',
            location='Test Location',
            address='123 Test St',
            property_type='house',
            price=100.0,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )
        self.valid_data = {
            'listing': self.listing.id,
            'start_date': (timezone.now().date() + timedelta(days=10)).isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=20)).isoformat(),
        }
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/bookings/create/')

    def test_required_fields(self):
        self.request.user = self.user
        view_mock = Mock()
        view_mock.kwargs = {'listing_id': self.listing.id}
        serializer = BookingCreateSerializer(data={}, context={'request': self.request, 'view': view_mock})
        self.assertFalse(serializer.is_valid())
        required_fields = ['start_date', 'end_date']  # Убираем listing, так как он берется из URL
        for field in required_fields:
            self.assertIn(field, serializer.errors)

    def test_field_validation(self):
        invalid_data = self.valid_data.copy()
        invalid_data['start_date'] = 'invalid_date'  # Некорректный формат даты
        invalid_data['end_date'] = 'invalid_date'
        serializer = BookingCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('start_date', serializer.errors)
        self.assertIn('end_date', serializer.errors)

    def test_create_booking(self):
        self.request.user = self.user
        view_mock = Mock()
        view_mock.kwargs = {'listing_id': self.listing.id}
        serializer = BookingCreateSerializer(data=self.valid_data, context={'request': self.request, 'view': view_mock})
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        self.assertEqual(booking.listing, self.listing)
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.start_date.isoformat(), self.valid_data['start_date'])
        self.assertEqual(booking.end_date.isoformat(), self.valid_data['end_date'])

    def test_create_booking_with_listing_id_in_url(self):
        # Если пользователь не администратор, использовать listing_id из URL
        self.request.user = self.user
        view_mock = Mock()
        view_mock.kwargs = {'listing_id': self.listing.id}
        serializer = BookingCreateSerializer(data={'start_date': self.valid_data['start_date'], 'end_date': self.valid_data['end_date']}, context={'request': self.request, 'view': view_mock})
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        self.assertEqual(booking.listing, self.listing)
        self.assertEqual(booking.user, self.user)

    def test_invalid_listing(self):
        # Проверка на случай несуществующего listing_id
        self.request.user = self.user
        invalid_data = self.valid_data.copy()
        invalid_data['listing'] = 9999  # Несуществующий listing_id
        serializer = BookingCreateSerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('listing', serializer.errors)

    def test_unavailable_dates(self):
        self.request.user = self.user
        # Создаем другое бронирование на те же даты, чтобы сделать их недоступными
        Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=20),
            status=BookingStatusChoices.CONFIRMED
        )
        # Добавляем mock view в контекст
        view_mock = Mock()
        view_mock.kwargs = {'listing_id': self.listing.id}
        serializer = BookingCreateSerializer(data=self.valid_data, context={'request': self.request, 'view': view_mock})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
