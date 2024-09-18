from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from django.core.exceptions import ValidationError
from datetime import date, timedelta, datetime
from django.utils import timezone
from unittest.mock import patch

User = get_user_model()


class BookingExceptionsTest(TestCase):
    def setUp(self):
        # Создание пользователей
        self.business_user = User.objects.create_user(
            email='business@example.com',
            username='business_user',
            password='password123',
            is_business_account=True
        )
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            username='regular_user',
            password='password123',
            is_business_account=False
        )
        # Создание объявления
        self.listing = Listing.objects.create(
            owner=self.business_user,
            title='Test Listing',
            description='A test listing',
            location='Test Location',
            address='123 Test Street',
            property_type='HOUSE',
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )
        self.today = date.today()
        self.max_date = self.today + timedelta(days=90)

    def test_booking_without_listing(self):
        """
        Проверка, что бронирование без listing вызывает IntegrityError.
        """
        booking = Booking(
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.CONFIRMED
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_booking_without_user(self):
        """
        Проверка, что бронирование без user вызывает IntegrityError.
        """
        booking = Booking(
            listing=self.listing,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.CONFIRMED
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    @patch('django.utils.timezone.now')
    def test_booking_with_invalid_status(self, mock_now):
        """
        Проверка, что бронирование с невалидным статусом вызывает ValidationError.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=999  # Невалидный статус
        )
        with patch.object(self.listing, 'is_available', return_value=True):
            with self.assertRaises(ValidationError):
                booking.full_clean()
