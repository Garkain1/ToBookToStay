from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.bookings.forms import BookingAdminForm
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.users.models import User


class BookingAdminFormTests(TestCase):
    def setUp(self):
        # Создаем пользователя и листинг
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
            location='Test location',
            address='Test address',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )

    def test_valid_form(self):
        """Проверка, что форма валидна при корректных данных."""
        today = timezone.now().date()
        data = {
            'listing': self.listing.id,
            'user': self.user.id,
            'start_date': today + timedelta(days=10),
            'end_date': today + timedelta(days=15),
            'status_choice': BookingStatusChoices.CONFIRMED,
            'is_soft_deleted': False,
            'total_price': 500.0,  # Добавляем total_price
        }
        form = BookingAdminForm(data=data)
        self.assertTrue(form.is_valid())
        booking = form.save(commit=False)
        self.assertEqual(str(booking.status), str(BookingStatusChoices.CONFIRMED))  # Преобразуем к строке

    def test_soft_delete_checked(self):
        """Проверка, что при установке soft_delete статус становится DELETED."""
        today = timezone.now().date()
        data = {
            'listing': self.listing.id,
            'user': self.user.id,
            'start_date': today + timedelta(days=10),
            'end_date': today + timedelta(days=15),
            'status_choice': BookingStatusChoices.CONFIRMED,
            'is_soft_deleted': True,
            'total_price': 500.0,  # Добавляем total_price
        }
        form = BookingAdminForm(data=data)
        self.assertTrue(form.is_valid())
        booking = form.save(commit=False)
        self.assertEqual(str(booking.status), str(BookingStatusChoices.DELETED))  # Преобразуем к строке

    def test_soft_delete_unchecked(self):
        """Проверка, что при снятии soft_delete статус устанавливается согласно status_choice."""
        today = timezone.now().date()
        data = {
            'listing': self.listing.id,
            'user': self.user.id,
            'start_date': today + timedelta(days=10),
            'end_date': today + timedelta(days=15),
            'status_choice': BookingStatusChoices.CONFIRMED,
            'is_soft_deleted': False,
            'total_price': 500.0,  # Добавляем total_price
        }
        form = BookingAdminForm(data=data)
        self.assertTrue(form.is_valid())
        booking = form.save(commit=False)
        self.assertEqual(str(booking.status), str(BookingStatusChoices.CONFIRMED))

    def test_start_date_in_past(self):
        """Проверка, что нельзя установить start_date в прошлом."""
        past_start_date = timezone.now().date() - timedelta(days=10)
        past_end_date = timezone.now().date() - timedelta(days=5)
        data = {
            'listing': self.listing.id,
            'user': self.user.id,
            'start_date': past_start_date,
            'end_date': past_end_date,
            'status_choice': BookingStatusChoices.PENDING,
            'is_soft_deleted': False,
            'total_price': 500.0,
        }
        form = BookingAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Start date cannot be in the past.', form.errors['__all__'])

    def test_start_date_exceeds_90_days(self):
        """Проверка, что нельзя установить start_date более чем через 90 дней."""
        today = timezone.now().date()
        start_date = today + timedelta(days=91)
        end_date = start_date + timedelta(days=5)
        data = {
            'listing': self.listing.id,
            'user': self.user.id,
            'start_date': start_date,
            'end_date': end_date,
            'status_choice': BookingStatusChoices.PENDING,
            'is_soft_deleted': False,
            'total_price': 500.0,
        }
        form = BookingAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Start date cannot be more than 90 days from today.', form.errors['__all__'])

    def test_overlapping_booking(self):
        """Проверка, что нельзя создать бронирование, пересекающееся с существующими."""
        # Создаем существующее бронирование
        existing_booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=15),
            status=BookingStatusChoices.CONFIRMED,
            total_price=500.0
        )

        # Попытка создать пересекающееся бронирование
        overlapping_start = timezone.now().date() + timedelta(days=12)
        overlapping_end = timezone.now().date() + timedelta(days=18)
        data = {
            'listing': self.listing.id,
            'user': self.user.id,
            'start_date': overlapping_start,
            'end_date': overlapping_end,
            'status_choice': BookingStatusChoices.PENDING,
            'is_soft_deleted': False,

        }
        form = BookingAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Selected dates are not available.', form.errors['__all__'])
