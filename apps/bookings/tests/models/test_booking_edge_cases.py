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


class BookingEdgeCasesTest(TestCase):
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

    @patch('django.utils.timezone.now')
    def test_start_date_equals_today(self, mock_now):
        """
        Проверка, что бронирование с start_date = today успешно создается.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today,
            end_date=self.today + timedelta(days=2),
            total_price=200.00,
            status=BookingStatusChoices.CONFIRMED
        )
        # Предположим, что доступность возвращает True
        with patch.object(self.listing, 'is_available', return_value=True):
            try:
                booking.full_clean()
                booking.save()
            except ValidationError:
                self.fail("Booking с start_date = today не должен вызывать ValidationError.")

    @patch('django.utils.timezone.now')
    def test_start_date_equals_max_date(self, mock_now):
        """
        Проверка, что бронирование с start_date = today + 90 дней успешно создается.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.max_date,
            end_date=self.max_date + timedelta(days=1),
            total_price=100.00,
            status=BookingStatusChoices.CONFIRMED
        )
        # Предположим, что доступность возвращает True
        with patch.object(self.listing, 'is_available', return_value=True):
            try:
                booking.full_clean()
                booking.save()
            except ValidationError:
                self.fail("Booking с start_date = max_date не должен вызывать ValidationError.")

    @patch('django.utils.timezone.now')
    def test_start_date_over_max_date(self, mock_now):
        """
        Проверка, что бронирование с start_date > today + 90 дней вызывает ValidationError.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.max_date + timedelta(days=1),
            end_date=self.max_date + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.CONFIRMED
        )
        with patch.object(self.listing, 'is_available', return_value=True):
            with self.assertRaises(ValidationError) as context:
                booking.full_clean()
            self.assertIn('Start date cannot be more than 90 days from today.',
                          context.exception.message_dict['__all__'])

    @patch('django.utils.timezone.now')
    def test_start_date_equals_end_date(self, mock_now):
        """
        Проверка, что бронирование с start_date = end_date вызывает ValidationError.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=1),
            total_price=0.00,
            status=BookingStatusChoices.CONFIRMED
        )
        with patch.object(self.listing, 'is_available', return_value=True):
            with self.assertRaises(ValidationError) as context:
                booking.full_clean()
            self.assertIn('Start date must be before end date.', context.exception.message_dict['__all__'])

    @patch('django.utils.timezone.now')
    def test_leap_year_booking(self, mock_now):
        """
        Проверка корректной обработки 29 февраля в високосный год.
        """
        # Установка фиктивной сегодняшней даты на 28 февраля 2024 года (високосный год)
        mock_now.return_value = timezone.make_aware(datetime.combine(date(2024, 2, 28), datetime.min.time()))
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=date(2024, 2, 29),
            end_date=date(2024, 3, 1),
            total_price=100.00,
            status=BookingStatusChoices.CONFIRMED
        )
        with patch.object(self.listing, 'is_available', return_value=True):
            try:
                booking.full_clean()
                booking.save()
            except ValidationError:
                self.fail("Booking с датой 29 февраля не должен вызывать ValidationError в високосный год.")
