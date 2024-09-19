from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class AvailableDatesByMonthViewTests(APITestCase):

    def setUp(self):
        # Создаем пользователя и листинг
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',  # Указываем email
            password='testpass',
            is_business_account=True
        )
        self.listing = Listing.objects.create(
            owner=self.user,
            title='Test Listing',
            description='Test description',
            location='Test City',
            address='123 Test St',
            property_type='Apartment',
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.ACTIVE,  # Предполагаем, что 1 - это статус ACTIVE
        )

    def test_available_dates_no_bookings(self):
        """
        Тест, когда нет бронирований - должен вернуть все доступные даты в пределах 90 дней.
        """
        url = reverse('available-dates-by-month', args=[self.listing.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_dates_by_month', response.data)
        # Проверяем, что даты возвращаются в виде списка
        self.assertIsInstance(response.data['available_dates_by_month'], list)
        # Проверяем, что возвращены данные за все 3 месяца (примерная проверка)
        self.assertGreaterEqual(len(response.data['available_dates_by_month']), 1)

    def test_available_dates_with_bookings(self):
        """
        Тест, когда существуют бронирования - проверка на исключение занятых дат.
        """
        today = timezone.now().date()
        # Создаем бронирование, перекрывающее часть диапазона
        Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=10),
            total_price=500,
            status=BookingStatusChoices.CONFIRMED,
        )

        url = reverse('available-dates-by-month', args=[self.listing.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_dates_by_month', response.data)
        # Проверяем, что забронированные даты отсутствуют в доступных датах
        available_dates = [date for month in response.data['available_dates_by_month'] for date in month['dates']]
        for day in range(5, 10):
            self.assertNotIn((today + timedelta(days=day)).strftime('%Y-%m-%d'), available_dates)

    def test_invalid_listing(self):
        """
        Тест с некорректным ID листинга - должен вернуть 404.
        """
        url = reverse('available-dates-by-month', args=[9999])  # Используем несуществующий ID
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Listing not found')

    def test_pagination_of_available_dates(self):
        """
        Тест проверки пагинации дат.
        """
        url = reverse('available-dates-by-month', args=[self.listing.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_dates_by_month', response.data)

        # Проверяем, что данные разделены по месяцам
        self.assertTrue(all('month' in month for month in response.data['available_dates_by_month']))
        self.assertTrue(all('dates' in month for month in response.data['available_dates_by_month']))

        # Проверяем, что в каждом месяце есть корректные даты
        for month in response.data['available_dates_by_month']:
            self.assertIsInstance(month['dates'], list)
