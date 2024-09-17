from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.listings.models import Listing
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class TestListingUpdateView(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='password',
            is_business_account=False
        )
        self.business_user = User.objects.create_user(
            email='business@example.com',
            username='business_user',
            password='password',
            is_business_account=True
        )
        self.other_business_user = User.objects.create_user(
            email='other_business@example.com',
            username='other_business_user',
            password='password',
            is_business_account=True
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin_user',
            password='password'
        )

        # Создаем тестовое объявление
        self.listing = Listing.objects.create(
            title='Test Listing',
            description='Test Description',
            location='Berlin',
            address='Test Address',
            property_type=PropertyTypeChoices.APARTMENT,
            price=500000,
            rooms=3,
            owner=self.business_user,
            status=ListingStatusChoices.ACTIVE
        )

        self.url = reverse('listing-update', kwargs={'id': self.listing.id})

    def test_update_listing_unauthenticated_user(self):
        # Попытка обновления объявления неаутентифицированным пользователем
        response = self.client.put(self.url, {'title': 'Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_listing_non_business_user(self):
        # Попытка обновления объявления обычным пользователем
        self.client.login(email='user@example.com', password='password')
        response = self.client.put(self.url, {'title': 'Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_listing_business_user_owner(self):
        # Обновление объявления владельцем с бизнес-аккаунтом
        self.client.login(email='business@example.com', password='password')
        response = self.client.patch(self.url, {'title': 'Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Updated Title')

    def test_update_listing_other_business_user(self):
        # Попытка обновления объявления другого пользователя бизнес-пользователем
        self.client.login(email='other_business@example.com', password='password')
        response = self.client.patch(self.url, {'title': 'Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_listing_admin(self):
        # Обновление объявления администратором
        self.client.login(email='admin@example.com', password='password')
        response = self.client.patch(self.url, {'title': 'Admin Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Admin Updated Title')

    def test_update_deleted_listing_by_non_admin(self):
        # Попытка обновления мягко удаленного объявления не администратором
        self.listing.status = ListingStatusChoices.DELETED
        self.listing.save()
        self.client.login(email='business@example.com', password='password')
        response = self.client.patch(self.url, {'title': 'Trying to update deleted'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_deleted_listing_by_admin(self):
        # Обновление мягко удаленного объявления администратором
        self.listing.status = ListingStatusChoices.DELETED
        self.listing.save()
        self.client.login(email='admin@example.com', password='password')
        response = self.client.patch(self.url, {'title': 'Admin Updated Deleted Listing'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Admin Updated Deleted Listing')

    def test_update_listing_invalid_data(self):
        # Отправка некорректных данных
        self.client.login(email='business@example.com', password='password')
        response = self.client.patch(self.url, {'price': 'invalid_price'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_vs_full_update(self):
        # Проверка частичного и полного обновления
        self.client.login(email='business@example.com', password='password')

        # Частичное обновление
        response = self.client.patch(self.url, {'title': 'Partially Updated Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Partially Updated Title')

        # Полное обновление
        response = self.client.put(self.url, {
            'title': 'Fully Updated Title',
            'description': 'Updated Description',
            'location': 'Munich',
            'address': 'Updated Address',
            'property_type': PropertyTypeChoices.HOUSE,
            'price': 750000,
            'rooms': 5,
            'owner': self.business_user.id  # Полное обновление требует всех полей
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Fully Updated Title')
        self.assertEqual(self.listing.location, 'Munich')
        self.assertEqual(self.listing.rooms, 5)
