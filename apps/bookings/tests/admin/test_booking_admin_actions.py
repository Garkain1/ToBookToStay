from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices
from apps.users.models import User


class TestBookingAdminActions(TestCase):
    def setUp(self):
        # Создаем суперпользователя для админки
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin@example.com', password='adminpass')

        # Создаем обычного пользователя и листинг
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )

        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='123 Main St',
            address='123 Main St',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )

        # Создаем бронирования
        self.booking1 = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=5),
            end_date=timezone.now().date() + timedelta(days=10),
            status=BookingStatusChoices.PENDING,
            total_price=500.0
        )

        self.booking2 = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=15),
            end_date=timezone.now().date() + timedelta(days=20),
            status=BookingStatusChoices.PENDING,
            total_price=500.0
        )

    def test_make_requested_action(self):
        url = reverse('admin:bookings_booking_changelist')
        data = {
            'action': 'make_requested',
            '_selected_action': [self.booking1.pk, self.booking2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'REQUEST'
        self.booking1.refresh_from_db()
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking1.status, BookingStatusChoices.REQUEST)
        self.assertEqual(self.booking2.status, BookingStatusChoices.REQUEST)

    def test_make_confirmed_action(self):
        url = reverse('admin:bookings_booking_changelist')
        data = {
            'action': 'make_confirmed',
            '_selected_action': [self.booking1.pk, self.booking2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'CONFIRMED'
        self.booking1.refresh_from_db()
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking1.status, BookingStatusChoices.CONFIRMED)
        self.assertEqual(self.booking2.status, BookingStatusChoices.CONFIRMED)

    def test_make_completed_action(self):
        url = reverse('admin:bookings_booking_changelist')
        data = {
            'action': 'make_completed',
            '_selected_action': [self.booking1.pk, self.booking2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'COMPLETED'
        self.booking1.refresh_from_db()
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking1.status, BookingStatusChoices.COMPLETED)
        self.assertEqual(self.booking2.status, BookingStatusChoices.COMPLETED)

    def test_make_canceled_action(self):
        url = reverse('admin:bookings_booking_changelist')
        data = {
            'action': 'make_canceled',
            '_selected_action': [self.booking1.pk, self.booking2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'CANCELED'
        self.booking1.refresh_from_db()
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking1.status, BookingStatusChoices.CANCELED)
        self.assertEqual(self.booking2.status, BookingStatusChoices.CANCELED)

    def test_make_deleted_action(self):
        url = reverse('admin:bookings_booking_changelist')
        data = {
            'action': 'make_deleted',
            '_selected_action': [self.booking1.pk, self.booking2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'DELETED'
        self.booking1.refresh_from_db()
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking1.status, BookingStatusChoices.DELETED)
        self.assertEqual(self.booking2.status, BookingStatusChoices.DELETED)
