from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from django.core.exceptions import ValidationError
from datetime import date, timedelta, datetime
from unittest.mock import patch

User = get_user_model()


class BookingCleanMethodTest(TestCase):
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

    def create_booking_instance(self, start_offset, end_offset, status=BookingStatusChoices.PENDING):
        """
        Вспомогательный метод для создания экземпляра бронирования без сохранения.
        """
        start_date = self.today + timedelta(days=start_offset)
        end_date = self.today + timedelta(days=end_offset)
        booking = Booking(
            listing=self.listing,
            user=self.regular_user,
            start_date=start_date,
            end_date=end_date,
            total_price=100.00,
            status=status
        )
        return booking

    @patch('django.utils.timezone.now')
    def test_clean_valid_booking(self, mock_now):
        """
        Проверка, что корректное бронирование проходит валидацию.
        """
        mock_now.return_value = datetime.combine(self.today, datetime.min.time())
        booking = self.create_booking_instance(1, 3, status=BookingStatusChoices.CONFIRMED)
        # Предположим, что доступность возвращает True
        with patch.object(self.listing, 'is_available', return_value=True):
            try:
                booking.full_clean()
            except ValidationError:
                self.fail("ValidationError не должно возникать для корректного бронирования.")

    @patch('django.utils.timezone.now')
    def test_clean_start_date_after_end_date(self, mock_now):
        """
        Проверка, что бронирование с start_date >= end_date вызывает ValidationError.
        """
        mock_now.return_value = datetime.combine(self.today, datetime.min.time())
        booking = self.create_booking_instance(5, 5, status=BookingStatusChoices.CONFIRMED)
        with patch.object(self.listing, 'is_available', return_value=True):
            with self.assertRaises(ValidationError) as context:
                booking.full_clean()
            self.assertIn('Start date must be before end date.', context.exception.message_dict['__all__'])

    @patch('django.utils.timezone.now')
    def test_clean_start_date_in_past(self, mock_now):
        """
        Проверка, что бронирование с start_date в прошлом вызывает ValidationError.
        """
        mock_now.return_value = datetime.combine(self.today, datetime.min.time())
        booking = self.create_booking_instance(-1, 2, status=BookingStatusChoices.CONFIRMED)
        with patch.object(self.listing, 'is_available', return_value=True):
            with self.assertRaises(ValidationError) as context:
                booking.full_clean()
            self.assertIn('Start date cannot be in the past.', context.exception.message_dict['__all__'])

    @patch('django.utils.timezone.now')
    def test_clean_start_date_exceeds_max_date(self, mock_now):
        """
        Проверка, что бронирование с start_date > today + 90 дней вызывает ValidationError.
        """
        mock_now.return_value = datetime.combine(self.today, datetime.min.time())
        booking = self.create_booking_instance(91, 95, status=BookingStatusChoices.CONFIRMED)
        with patch.object(self.listing, 'is_available', return_value=True):
            with self.assertRaises(ValidationError) as context:
                booking.full_clean()
            self.assertIn('Start date cannot be more than 90 days from today.',
                          context.exception.message_dict['__all__'])

    @patch('django.utils.timezone.now')
    def test_clean_is_available_false(self, mock_now):
        """
        Проверка, что бронирование с недоступными датами вызывает ValidationError.
        """
        mock_now.return_value = datetime.combine(self.today, datetime.min.time())
        booking = self.create_booking_instance(10, 15, status=BookingStatusChoices.CONFIRMED)
        with patch.object(self.listing, 'is_available', return_value=False):
            with self.assertRaises(ValidationError) as context:
                booking.full_clean()
            self.assertIn('Selected dates are not available.', context.exception.message_dict['__all__'])
