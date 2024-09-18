from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from datetime import date, timedelta

User = get_user_model()


class BookingStrMethodTest(TestCase):
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

    def test_str_method(self):
        """
        Проверка корректного строкового представления объекта Booking.
        """
        booking = Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
            total_price=100.00,
            status=BookingStatusChoices.CONFIRMED
        )
        expected_str = f'Booking {booking.id} for {self.listing.title}'
        self.assertEqual(str(booking), expected_str, "__str__() должен возвращать корректное строковое представление.")
