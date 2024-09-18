from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.users.models import User


class BookingAdminGeneralTests(TestCase):
    def setUp(self):
        # Создание суперпользователя
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin@example.com', password='adminpass')

        # Создаем обычного пользователя и объявления
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='userpass',
            is_business_account=True
        )

        self.listing1 = Listing.objects.create(
            title='Test Listing 1',
            owner=self.user,
            description='Test description 1',
            location='Test location 1',
            address='123 Main St',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )

        self.listing2 = Listing.objects.create(
            title='Test Listing 2',
            owner=self.user,
            description='Test description 2',
            location='Test location 2',
            address='456 Elm St',
            property_type='apartment',
            price=200.0,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

        # Создаем бронирования
        today = timezone.now().date()
        self.booking1 = Booking.objects.create(
            listing=self.listing1,
            user=self.user,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=15),
            status=BookingStatusChoices.CONFIRMED,
            total_price=500.0
        )

        self.booking2 = Booking.objects.create(
            listing=self.listing2,
            user=self.user,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=25),
            status=BookingStatusChoices.REQUEST,
            total_price=1000.0
        )

    def test_booking_changelist_page(self):
        """
        Проверяем доступность страницы списка бронирований в админке.
        """
        url = reverse('admin:bookings_booking_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_booking_add_page(self):
        """
        Проверяем доступность страницы добавления нового бронирования в админке.
        """
        url = reverse('admin:bookings_booking_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_booking_change_page(self):
        """
        Проверяем доступность страницы редактирования бронирования в админке.
        """
        url = reverse('admin:bookings_booking_change', args=[self.booking1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_filter_functionality(self):
        """
        Проверяем, что фильтры в админке работают корректно.
        """
        url = reverse('admin:bookings_booking_changelist')

        # Применяем фильтр по статусу 'CONFIRMED'
        response = self.client.get(url, {'status': BookingStatusChoices.CONFIRMED})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Booking {self.booking1.id}')
        self.assertNotContains(response, f'Booking {self.booking2.id}')

        # Применяем фильтр по статусу 'REQUEST'
        response = self.client.get(url, {'status': BookingStatusChoices.REQUEST})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Booking {self.booking2.id}')
        self.assertNotContains(response, f'Booking {self.booking1.id}')

    def test_search_fields_functionality(self):
        """
        Проверяем, что поиск в админке работает корректно.
        """
        url = reverse('admin:bookings_booking_changelist')

        # Поиск по строковому представлению бронирования
        response = self.client.get(url, {'q': str(self.booking1)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Booking {self.booking1.id}')
        self.assertNotContains(response, f'Booking {self.booking2.id}')

        # Поиск по названию листинга
        response = self.client.get(url, {'q': self.listing2.title})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Booking {self.booking2.id}')
        self.assertNotContains(response, f'Booking {self.booking1.id}')

        # Поиск по имени пользователя
        response = self.client.get(url, {'q': self.user.username})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Booking {self.booking1.id}')
        self.assertContains(response, f'Booking {self.booking2.id}')

    def test_booking_admin_create_past_booking(self):
        """
        Проверяем, что админка не позволяет создать бронирование с датами в прошлом.
        """
        url = reverse('admin:bookings_booking_add')
        past_start_date = timezone.now().date() - timedelta(days=10)
        past_end_date = timezone.now().date() - timedelta(days=5)

        data = {
            'listing': self.listing1.id,
            'user': self.user.id,
            'start_date': past_start_date,
            'end_date': past_end_date,
            'status': BookingStatusChoices.PENDING,
            'status_choice': BookingStatusChoices.PENDING,  # Предполагается, что форма использует 'status_choice'
            'is_soft_deleted': False,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Форма возвращает ошибки, остается на странице добавления
        form = response.context['adminform'].form
        self.assertIn('__all__', form.errors)
        self.assertIn('Start date cannot be in the past.', form.errors['__all__'])

    def test_booking_admin_create_booking_exceeding_90_days(self):
        """
        Проверяем, что админка не позволяет создать бронирование с датами, превышающими 90 дней.
        """
        url = reverse('admin:bookings_booking_add')
        today = timezone.now().date()
        start_date = today + timedelta(days=91)
        end_date = start_date + timedelta(days=5)

        data = {
            'listing': self.listing1.id,
            'user': self.user.id,
            'start_date': start_date,
            'end_date': end_date,
            'status': BookingStatusChoices.PENDING,
            'status_choice': BookingStatusChoices.PENDING,
            'is_soft_deleted': False,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertIn('__all__', form.errors)
        self.assertIn('Start date cannot be more than 90 days from today.', form.errors['__all__'])

    def test_booking_admin_create_overlapping_booking(self):
        """
        Проверяем, что админка не позволяет создать бронирование, пересекающееся с существующими бронированиями.
        """
        url = reverse('admin:bookings_booking_add')
        today = timezone.now().date()
        overlapping_start = today + timedelta(days=12)
        overlapping_end = today + timedelta(days=18)

        data = {
            'listing': self.listing1.id,
            'user': self.user.id,
            'start_date': overlapping_start,
            'end_date': overlapping_end,
            'status': BookingStatusChoices.PENDING,
            'status_choice': BookingStatusChoices.PENDING,
            'is_soft_deleted': False,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertIn('__all__', form.errors)
        self.assertIn('Selected dates are not available.', form.errors['__all__'])
