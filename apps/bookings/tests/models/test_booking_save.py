from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from datetime import date, timedelta, datetime
from django.utils import timezone
from unittest.mock import patch
from decimal import Decimal
from time import sleep

User = get_user_model()


class BookingSaveMethodTest(TestCase):
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

    def create_booking(self, start_offset, end_offset, status=BookingStatusChoices.PENDING):
        """
        Вспомогательный метод для создания и сохранения бронирования.
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
        booking.save()
        return booking

    @patch('django.utils.timezone.now')
    def test_save_create_booking_sets_total_price_correctly(self, mock_now):
        """
        Проверка, что при создании бронирования total_price рассчитывается корректно.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(1, 4)  # 3 дня
        expected_total = self.listing.price * 3
        self.assertEqual(booking.total_price, expected_total,
                         "Total price должен быть равен цене за день * количество дней.")

    @patch('django.utils.timezone.now')
    def test_save_update_booking_status_changes_status_changed_at(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(1, 4, status=BookingStatusChoices.PENDING)

        # Проверяем, что `status_changed_at` изначально `None`
        old_status_changed_at = booking.status_changed_at
        self.assertIsNone(old_status_changed_at, "status_changed_at должно быть None при создании нового бронирования.")

        # Изменение статуса
        booking.status = BookingStatusChoices.CONFIRMED
        booking.save()
        booking.refresh_from_db()

        # Теперь проверяем, что `status_changed_at` больше не None
        self.assertIsNotNone(booking.status_changed_at,
                             "status_changed_at должно быть установлено при изменении статуса.")
        self.assertTrue(booking.status_changed_at >= mock_now.return_value,
                        "Поле status_changed_at должно обновиться при изменении статуса.")

    @patch('django.utils.timezone.now')
    def test_save_update_booking_dates_changes_total_price(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(1, 4)  # 3 дня, total_price=300

        # Изменяем даты бронирования, теперь 2 дня
        booking.start_date += timedelta(days=1)  # Новые даты: 2 дня
        booking.end_date += timedelta(days=1)
        booking.save()

        # Пересчет ожидаемой цены
        days = (booking.end_date - booking.start_date).days
        expected_total = Decimal(self.listing.price * days)

        self.assertEqual(booking.total_price, expected_total,
                         "Total price должен быть пересчитан при изменении количества дней.")

    @patch('django.utils.timezone.now')
    def test_save_update_booking_listing_price_changes_total_price(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(1, 4)  # 3 дня, total_price=300

        # Изменение цены в объявлении
        self.listing.price = Decimal('150.00')
        self.listing.save()

        # Изменяем даты бронирования, теперь 2 дня
        booking.start_date += timedelta(days=1)  # Новые даты: 2 дня
        booking.end_date += timedelta(days=1)
        booking.save()

        # Обновляем объект `listing` в бронировании
        booking.listing.refresh_from_db()

        booking.save()

        # Пересчет ожидаемой цены
        days = (booking.end_date - booking.start_date).days
        expected_total = Decimal(self.listing.price * days)

        self.assertEqual(booking.total_price, expected_total,
                         "Total price должен быть пересчитан при изменении цены объявления.")

    @patch('django.utils.timezone.now')
    def test_save_no_changes_does_not_change_total_price(self, mock_now):
        """
        Проверка, что при сохранении без изменений total_price остается прежним.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(1, 4)  # 3 дня, total_price=300
        old_total_price = booking.total_price
        booking.save()
        booking.refresh_from_db()
        self.assertEqual(booking.total_price, old_total_price,
                         "Total price не должен изменяться при сохранении без изменений.")
