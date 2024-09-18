from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from datetime import date, timedelta, datetime
from decimal import Decimal

User = get_user_model()


class BookingFieldsTest(TestCase):
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

    def test_field_presence(self):
        """
        Проверка наличия всех обязательных полей в модели Booking.
        """
        booking = Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.PENDING
        )
        self.assertIsNotNone(booking.listing)
        self.assertIsNotNone(booking.user)
        self.assertIsNotNone(booking.start_date)
        self.assertIsNotNone(booking.end_date)
        self.assertIsNotNone(booking.total_price)
        self.assertIsNotNone(booking.status)
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)
        self.assertIsNone(booking.status_changed_at)

    def test_field_types(self):
        """
        Проверка типов данных полей модели Booking.
        """
        booking = Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.PENDING
        )
        self.assertIsInstance(booking.listing, Listing)
        self.assertIsInstance(booking.user, User)
        self.assertIsInstance(booking.start_date, date)
        self.assertIsInstance(booking.end_date, date)
        self.assertIsInstance(booking.total_price, Decimal)
        self.assertIsInstance(booking.status, int)
        self.assertIsInstance(booking.created_at, datetime)
        self.assertIsInstance(booking.updated_at, datetime)
        self.assertIsNone(booking.status_changed_at)

    def test_default_status(self):
        """
        Проверка значения по умолчанию для поля status.
        """
        booking = Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00
        )
        self.assertEqual(booking.status, BookingStatusChoices.PENDING)

    def test_auto_fields(self):
        """
        Проверка автоматического заполнения полей created_at, updated_at, status_changed_at.
        """
        booking = Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.PENDING
        )
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)
        self.assertIsNone(booking.status_changed_at)
