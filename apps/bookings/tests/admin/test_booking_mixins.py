from django.test import TestCase
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.bookings.mixins import StatusMixin, SoftDeleteMixin
from apps.users.models import User
from apps.listings.models import Listing


class TestBookingStatusMixin(TestCase, StatusMixin):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )

        # Создаем тестовый объект Listing
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='Test location',
            address='Test address',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )

        # Создаем тестовый объект Booking
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=5),
            status=BookingStatusChoices.PENDING,
            total_price=400.0
        )

    def test_status_display_pending(self):
        self.booking.status = BookingStatusChoices.PENDING
        self.booking.save()
        display = self.status_display(self.booking)
        self.assertIn('yellow', display)
        self.assertIn('Pending', strip_tags(display))

    def test_status_display_request(self):
        self.booking.status = BookingStatusChoices.REQUEST
        self.booking.save()
        display = self.status_display(self.booking)
        self.assertIn('blue', display)
        self.assertIn('Request', strip_tags(display))

    def test_status_display_confirmed(self):
        self.booking.status = BookingStatusChoices.CONFIRMED
        self.booking.save()
        display = self.status_display(self.booking)
        self.assertIn('green', display)
        self.assertIn('Confirmed', strip_tags(display))

    def test_status_display_completed(self):
        self.booking.status = BookingStatusChoices.COMPLETED
        self.booking.save()
        display = self.status_display(self.booking)
        self.assertIn('gray;', display)
        self.assertIn('Completed', strip_tags(display))

    def test_status_display_canceled(self):
        self.booking.status = BookingStatusChoices.CANCELED
        self.booking.save()
        display = self.status_display(self.booking)
        self.assertIn('red', display)
        self.assertIn('Canceled', strip_tags(display))


class TestBookingSoftDeleteMixin(TestCase, SoftDeleteMixin):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )

        # Создаем тестовый объект Listing
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='Test location',
            address='Test address',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )

        # Создаем тестовый объект Booking
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=5),
            status=BookingStatusChoices.PENDING,
            total_price=400.0
        )

    def test_is_soft_deleted_true(self):
        self.booking.status = BookingStatusChoices.DELETED
        self.booking.save()
        self.assertTrue(self.is_soft_deleted(self.booking))

    def test_is_soft_deleted_false_pending(self):
        self.booking.status = BookingStatusChoices.PENDING
        self.booking.save()
        self.assertFalse(self.is_soft_deleted(self.booking))

    def test_is_soft_deleted_false_confirmed(self):
        self.booking.status = BookingStatusChoices.CONFIRMED
        self.booking.save()
        self.assertFalse(self.is_soft_deleted(self.booking))
