from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from apps.listings.models import Listing
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class TestListingCreateView(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(email='user@example.com', username='user', password='password')
        self.business_user = User.objects.create_user(email='business@example.com', username='business_user', password='password', is_business_account=True)
        self.admin_user = User.objects.create_superuser(email='admin@example.com', username='admin', password='password')

    def test_create_listing_unauthenticated(self):
        # Попытка создания объявления неаутентифицированным пользователем
        url = reverse('listing-create')
        data = {
            'title': 'Test Listing',
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': 500000,
            'rooms': 3,
            'status': ListingStatusChoices.ACTIVE
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_listing_non_business_user(self):
        # Попытка создания объявления аутентифицированным не-бизнес пользователем
        self.client.login(email='user@example.com', password='password')
        url = reverse('listing-create')
        data = {
            'title': 'Test Listing',
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': 500000,
            'rooms': 3,
            'status': ListingStatusChoices.ACTIVE
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_listing_business_user(self):
        # Создание объявления аутентифицированным бизнес-пользователем
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-create')
        data = {
            'title': 'Test Listing',
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': 500000,
            'rooms': 3,
            'status': ListingStatusChoices.ACTIVE
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.count(), 1)
        self.assertEqual(Listing.objects.first().owner, self.business_user)

    def test_create_listing_admin_user(self):
        # Создание объявления аутентифицированным администратором
        self.client.login(email='admin@example.com', password='password')
        url = reverse('listing-create')
        data = {
            'title': 'Test Listing',
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': 500000,
            'rooms': 3,
            'owner': self.business_user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.count(), 1)
        self.assertEqual(Listing.objects.first().owner, self.business_user)

    def test_create_listing_admin_user_invalid_owner(self):
        # Попытка создания объявления администратором с назначением владельца, не являющегося бизнес-аккаунтом
        self.client.login(email='admin@example.com', password='password')
        url = reverse('listing-create')
        data = {
            'title': 'Test Listing',
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': 500000,
            'rooms': 3,
            'owner': self.user.id  # Попытка назначить обычного пользователя владельцем
        }
        response = self.client.post(url, data)
        # Проверяем, что запрос отклонен с ошибкой 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Проверяем, что в ответе присутствует сообщение об ошибке
        self.assertIn('owner', response.data)
        self.assertEqual(Listing.objects.count(), 0)

    def test_create_listing_invalid_data(self):
        # Отправка некорректных данных
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-create')
        data = {
            'title': '',  # Отсутствие обязательного поля title
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': '',  # Некорректное поле price
            'rooms': 3,
            'status': ListingStatusChoices.ACTIVE
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        self.assertIn('price', response.data)

    def test_create_listing_owner_assignment(self):
        # Проверка назначения владельца
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-create')
        data = {
            'title': 'Test Listing',
            'description': 'Description of the listing',
            'location': 'Berlin',
            'address': 'Address 1',
            'property_type': PropertyTypeChoices.APARTMENT,
            'price': 500000,
            'rooms': 3,
            'status': ListingStatusChoices.ACTIVE
        }
        response = self.client.post(url, data)
        listing = Listing.objects.first()
        self.assertEqual(listing.owner, self.business_user)
