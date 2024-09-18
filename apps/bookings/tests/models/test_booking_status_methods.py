from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from datetime import date, timedelta, datetime
from django.utils import timezone
from unittest.mock import patch

User = get_user_model()


class BookingStatusMethodsTest(TestCase):
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

    def create_booking(self, status=BookingStatusChoices.PENDING):
        """
        Вспомогательный метод для создания и сохранения бронирования.
        """
        booking = Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=3),
            total_price=200.00,
            status=status
        )
        return booking

    @patch('django.utils.timezone.now')
    def test_request_method(self, mock_now):
        """
        Проверка метода request().
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.PENDING)
        booking.request()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatusChoices.REQUEST, "Статус должен быть изменен на REQUEST.")

    @patch('django.utils.timezone.now')
    def test_confirm_method(self, mock_now):
        """
        Проверка метода confirm().
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.REQUEST)
        booking.confirm()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatusChoices.CONFIRMED, "Статус должен быть изменен на CONFIRMED.")

    @patch('django.utils.timezone.now')
    def test_complete_method(self, mock_now):
        """
        Проверка метода complete().
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.CONFIRMED)
        booking.complete()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatusChoices.COMPLETED, "Статус должен быть изменен на COMPLETED.")

    @patch('django.utils.timezone.now')
    def test_cancel_method(self, mock_now):
        """
        Проверка метода cancel().
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.CONFIRMED)
        booking.cancel()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatusChoices.CANCELED, "Статус должен быть изменен на CANCELED.")

    @patch('django.utils.timezone.now')
    def test_soft_delete_method(self, mock_now):
        """
        Проверка метода soft_delete().
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.CONFIRMED)
        booking.soft_delete()
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatusChoices.DELETED, "Статус должен быть изменен на DELETED.")

    @patch('django.utils.timezone.now')
    def test_status_changed_at_updates_on_status_change(self, mock_now):
        """
        Проверка обновления поля status_changed_at при изменении статуса.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.PENDING)
        old_status_changed_at = booking.status_changed_at
        booking.confirm()
        booking.refresh_from_db()
        self.assertNotEqual(booking.status_changed_at, old_status_changed_at,
                            "Поле status_changed_at должно обновиться при изменении статуса.")

    @patch('django.utils.timezone.now')
    def test_status_changed_at_not_updates_without_status_change(self, mock_now):
        """
        Проверка, что поле status_changed_at не обновляется при сохранении без изменения статуса.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        booking = self.create_booking(status=BookingStatusChoices.PENDING)
        old_status_changed_at = booking.status_changed_at
        # Сохранение без изменения статуса
        booking.save()
        booking.refresh_from_db()
        self.assertEqual(booking.status_changed_at, old_status_changed_at,
                         "Поле status_changed_at не должно обновляться без изменения статуса.")
