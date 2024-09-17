from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class TestMyListingsView(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.business_user = User.objects.create_user(
            email='business@example.com', username='business', password='password', is_business_account=True)
        self.other_business_user = User.objects.create_user(
            email='other_business@example.com', username='other_business', password='password', is_business_account=True)
        self.regular_user = User.objects.create_user(
            email='user@example.com', username='user', password='password')
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com', username='admin', password='password')

        # Создаем объявления
        self.listing1 = Listing.objects.create(
            title='Listing 1', description='Description 1', location='Berlin', address='Address 1',
            property_type=PropertyTypeChoices.APARTMENT, price=500000, rooms=3,
            status=ListingStatusChoices.ACTIVE, owner=self.business_user)
        self.listing2 = Listing.objects.create(
            title='Listing 2', description='Description 2', location='Munich', address='Address 2',
            property_type=PropertyTypeChoices.HOUSE, price=750000, rooms=5,
            status=ListingStatusChoices.DELETED, owner=self.business_user)

    def test_my_listings_unauthenticated_access(self):
        # Попытка доступа к "Моим" объявлениям неаутентифицированным пользователем
        url = reverse('my-listings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_listings_business_user(self):
        # Получение собственных объявлений аутентифицированным пользователем с бизнес-аккаунтом
        self.client.login(email='business@example.com', password='password')
        url = reverse('my-listings')
        response = self.client.get(url)
        self.assertTrue(self.client.login(email='business@example.com', password='password'))  # Проверка успешного логина
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Только активное объявление
        self.assertEqual(response.data['results'][0]['status'], ListingStatusChoices.ACTIVE)

    def test_my_listings_other_user_as_business(self):
        # Попытка получения объявлений другого пользователя аутентифицированным пользователем с бизнес-аккаунтом
        self.client.login(email='business@example.com', password='password')
        url = reverse('user-listings', kwargs={'user_id': self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Недостаточно прав доступа

    def test_my_listings_as_admin(self):
        # Получение любых объявлений аутентифицированным администратором
        self.client.login(email='admin@example.com', password='password')
        url = reverse('user-listings', kwargs={'user_id': self.business_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Включая мягко удаленные объявления

    def test_other_user_listings_as_regular_user(self):
        # Попытка получения объявлений другого пользователя аутентифицированным не-администратором
        self.client.login(email='user@example.com', password='password')
        url = reverse('user-listings', kwargs={'user_id': self.business_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Недостаточно прав доступа

    def test_my_listings_without_user_id(self):
        # Получение собственных объявлений без указания user_id
        self.client.login(email='business@example.com', password='password')
        url = reverse('my-listings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Только активное объявление

    def test_my_listings_exclude_deleted(self):
        # Проверка, что софт-удаленные объявления исключены для неадминистраторов
        self.client.login(email='business@example.com', password='password')
        url = reverse('my-listings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Только активное объявление

    def test_get_listings_non_existent_user(self):
        # Получение объявлений с несуществующим user_id
        self.client.login(email='admin@example.com', password='password')
        url = reverse('user-listings', kwargs={'user_id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_listings_without_user_id(self):
        # Проверка получения листинга администратором без передачи user_id
        self.client.login(email='admin@example.com', password='password')
        url = reverse('my-listings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Администратор видит все объявления

    def test_admin_listings_with_non_business_user(self):
        # Проверка получения листинга администратором для пользователя, не являющегося бизнес-аккаунтом
        self.client.login(email='admin@example.com', password='password')
        url = reverse('user-listings', kwargs={'user_id': self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
