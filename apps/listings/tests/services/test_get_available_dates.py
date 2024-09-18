from django.test import TestCase
from datetime import timedelta, datetime
from unittest.mock import patch
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.listings.services import get_available_dates

User = get_user_model()


class GetAvailableDatesTest(TestCase):
    def setUp(self):
        # Создание пользователя
        self.business_user = User.objects.create_user(
            email='business@example.com',
            username='business_user',
            password='password123',
            is_business_account=True
        )
        # Создание объявления (Listing)
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
        # Установка фиктивной сегодняшней даты
        self.today = datetime(2024, 2, 28).date()
        self.max_date = self.today + timedelta(days=90)

    def create_booking(self, start_offset, end_offset, status=BookingStatusChoices.CONFIRMED):
        start_date = self.today + timedelta(days=start_offset)
        end_date = self.today + timedelta(days=end_offset)
        Booking.objects.create(
            listing=self.listing,
            user=self.business_user,
            start_date=start_date,
            end_date=end_date,
            total_price=100.00 * (end_offset - start_offset),
            status=status
        )

    @patch('django.utils.timezone.now')
    def test_get_available_dates_no_bookings(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        available_dates = get_available_dates(self.listing)
        expected_dates = [self.today + timedelta(days=i) for i in range(90)]
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_with_single_booking(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        self.create_booking(10, 15)
        available_dates = get_available_dates(self.listing)
        excluded_dates = {self.today + timedelta(days=i) for i in range(10, 15)}
        expected_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_with_multiple_bookings(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        self.create_booking(5, 10)
        self.create_booking(20, 25, status=BookingStatusChoices.REQUEST)
        self.create_booking(30, 35)
        excluded_dates = set()
        for start, end in [(5, 10), (20, 25), (30, 35)]:
            excluded_dates.update({self.today + timedelta(days=i) for i in range(start, end)})
        expected_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        available_dates = get_available_dates(self.listing)
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_with_non_conflicting_status(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        self.create_booking(40, 45, status=BookingStatusChoices.CANCELED)
        self.create_booking(50, 55, status=BookingStatusChoices.COMPLETED)
        available_dates = get_available_dates(self.listing)
        expected_dates = [self.today + timedelta(days=i) for i in range(90)]
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_spanning_booking(self, mock_now):
        """
        Проверка списка доступных дат для бронирования, выходящего за границы максимального окна.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования, которое заканчивается после max_date
        self.create_booking(85, 90)
        excluded_dates = {self.today + timedelta(days=i) for i in range(85, 90)}
        expected_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        available_dates = get_available_dates(self.listing)
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_ends_today(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        self.create_booking(0, 1)
        available_dates = get_available_dates(self.listing)
        self.assertNotIn(self.today, available_dates)
        self.assertIn(self.today + timedelta(days=1), available_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_starts_on_max_date(self, mock_now):
        """
        Проверка доступности для бронирования, начинающегося на max_date.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования, которое начинается на max_date
        self.create_booking(89, 90)
        available_dates = get_available_dates(self.listing)
        self.assertNotIn(self.max_date, available_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_exactly_max_window(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        self.create_booking(0, 90)
        available_dates = get_available_dates(self.listing)
        for day in range(0, 90):
            self.assertNotIn(self.today + timedelta(days=day), available_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_exclude_booking_id(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(50, 55)
        available_dates = get_available_dates(self.listing)
        excluded_dates = {self.today + timedelta(days=i) for i in range(50, 55)}
        expected_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_non_overlapping_bookings(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        self.create_booking(10, 15)
        self.create_booking(20, 25)
        self.create_booking(30, 35)
        excluded_dates = {self.today + timedelta(days=i) for i in range(10, 15)} | \
                         {self.today + timedelta(days=i) for i in range(20, 25)} | \
                         {self.today + timedelta(days=i) for i in range(30, 35)}
        expected_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        available_dates = get_available_dates(self.listing)
        self.assertEqual(available_dates, expected_dates)

    @patch('django.utils.timezone.now')
    def test_get_available_dates_booking_exceeds_max_date(self, mock_now):
        """
        Проверка доступности для бронирования, превышающего 90-дневный лимит.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования, которое заканчивается на max_date
        self.create_booking(80, 90)
        excluded_dates = {self.today + timedelta(days=i) for i in range(80, 90)}
        expected_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        available_dates = get_available_dates(self.listing)
        self.assertEqual(available_dates, expected_dates)
