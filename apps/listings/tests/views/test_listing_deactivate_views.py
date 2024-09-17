from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class TestListingDeactivateView(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.business_user = User.objects.create_user(
            email='business@example.com', username='business', password='password', is_business_account=True)
        self.other_business_user = User.objects.create_user(
            email='other_business@example.com', username='other_business', password='password',
            is_business_account=True)
        self.regular_user = User.objects.create_user(
            email='user@example.com', username='user', password='password')
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com', username='admin', password='password')

        # Создаем объявления
        self.listing = Listing.objects.create(
            title='Listing 1', description='Description 1', location='Berlin', address='Address 1',
            property_type=PropertyTypeChoices.APARTMENT, price=500000, rooms=3,
            status=ListingStatusChoices.ACTIVE, owner=self.business_user)

    def test_deactivate_listing_unauthenticated_user(self):
        # Попытка активации неаутентифицированным пользователем
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deactivate_listing_regular_user(self):
        # Попытка активации обычным пользователем
        self.client.login(email='user@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_listing_business_user(self):
        # Активация объявления своим владельцем
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ListingStatusChoices.DEACTIVATED)

    def test_deactivate_other_user_listing_as_business(self):
        # Попытка активации объявления другого пользователя
        self.client.login(email='other_business@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_listing_admin_user(self):
        # Активация объявления администратором
        self.client.login(email='admin@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ListingStatusChoices.DEACTIVATED)

    def test_deactivate_deleted_listing(self):
        # Попытка активации мягко удаленного объявления
        self.listing.status = ListingStatusChoices.DELETED
        self.listing.save()
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivate_deleted_listing_admin_user(self):
        # Попытка активации мягко удаленного объявления
        self.listing.status = ListingStatusChoices.DELETED
        self.listing.save()
        self.client.login(email='admin@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_deactivation_action(self):
        # Отправка некорректного параметра действия
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': 9999})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_status_transition_verification(self):
        # Верификация перехода статуса
        self.client.login(email='business@example.com', password='password')
        url = reverse('listing-deactivate', kwargs={'id': self.listing.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Получаем объявление и проверяем статус
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ListingStatusChoices.DEACTIVATED)
