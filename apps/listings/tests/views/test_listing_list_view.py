from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices


class TestListingListView(APITestCase):

    def setUp(self):
        # Создаем пользователей с различными ролями
        self.admin_user = get_user_model().objects.create_user(
            username='adminuser', email='admin@example.com', password='admin123', is_staff=True
        )
        self.business_user = get_user_model().objects.create_user(
            username='businessuser', email='business@example.com', password='business123', is_business_account=True
        )
        self.regular_user = get_user_model().objects.create_user(
            username='regularuser', email='regular@example.com', password='regular123'
        )

        # Создаем 15 тестовых объявлений для проверки пагинации
        for i in range(15):
            Listing.objects.create(
                title=f'Listing {i + 1}',
                owner=self.business_user,
                description=f'Description {i + 1}',
                location='Berlin',
                address=f'Address {i + 1}',
                property_type=PropertyTypeChoices.APARTMENT,
                price=500000 + i * 1000,
                rooms=3,
                status=ListingStatusChoices.ACTIVE
            )

    def test_unauthenticated_user_access(self):
        response = self.client.get(reverse('listing-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 15)

        for listing in response.data['results']:
            self.assertIn('title', listing)

    def test_authenticated_non_admin_user_access(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('listing-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 15)

        for listing in response.data['results']:
            self.assertIn('title', listing)

    def test_authenticated_admin_user_access(self):
        # Тестируем доступ администратора
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('listing-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Проверка пагинации
        self.assertEqual(response.data['count'], 15)  # Проверка общего количества

    def test_pagination_second_page(self):
        # Проверка второй страницы
        response = self.client.get(reverse('listing-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # На второй странице должно быть оставшихся 5 объявлений
        self.assertEqual(len(response.data['results']), 5)

    def test_filter_by_price_range(self):
        # Тестируем фильтрацию по диапазону цен
        response = self.client.get(reverse('listing-list') + '?price_min=505000&price_max=514000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']),
                         10)  # Проверка количества объектов в фильтрации (с учетом пагинации)
        self.assertEqual(response.data['count'], 15)

    def test_filter_by_location(self):
        # Тестируем фильтрацию по местоположению
        response = self.client.get(reverse('listing-list') + '?location=Berlin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Первая страница с пагинацией
        self.assertEqual(response.data['count'], 15)  # Общее количество отфильтрованных объектов

    def test_filter_by_rooms_range(self):
        # Тестируем фильтрацию по количеству комнат
        response = self.client.get(reverse('listing-list') + '?rooms_min=2&rooms_max=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Первая страница с пагинацией
        self.assertEqual(response.data['count'], 15)  # Общее количество отфильтрованных объектов

    def test_filter_by_property_type(self):
        # Тестируем фильтрацию по типу недвижимости
        response = self.client.get(reverse('listing-list') + '?property_type=apartment')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Первая страница с пагинацией
        self.assertEqual(response.data['count'], 15)  # Общее количество отфильтрованных объектов

    def test_search_keyword(self):
        # Тестируем поиск по ключевому слову
        response = self.client.get(reverse('listing-list') + '?search=Listing')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Первая страница с пагинацией
        self.assertEqual(response.data['count'], 15)  # Общее количество отфильтрованных объектов

    def test_sorting_for_regular_user(self):
        # Тестируем сортировку для обычного пользователя
        response = self.client.get(reverse('listing-list') + '?ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что результаты отсортированы по цене
        prices = [item['price'] for item in response.data['results']]
        self.assertTrue(prices == sorted(prices))  # Сортировка в порядке возрастания

    def test_sorting_for_admin_user(self):
        # Тестируем сортировку для администратора
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('listing-list') + '?ordering=status')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что результаты отсортированы по статусу
        statuses = [item['status_display'] for item in response.data['results']]
        self.assertTrue(statuses == sorted(statuses))  # Проверка сортировки по статусу

    def test_combined_filter_and_sort_with_pagination(self):
        # Тестируем комбинированную фильтрацию, сортировку и пагинацию
        response = self.client.get(reverse('listing-list') + '?price_min=500000&ordering=-price&page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # На второй странице должно быть 5 объектов после сортировки
        self.assertEqual(len(response.data['results']), 5)

    def test_invalid_filter_params(self):
        # Тестируем некорректные параметры фильтрации
        response = self.client.get(reverse('listing-list') + '?price_min=abc&price_max=-500')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
