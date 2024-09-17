from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class TestListingDetailView(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(email='user@example.com', username='user', password='password')
        self.owner = User.objects.create_user(email='owner@example.com', username='owner', password='password')
        self.admin = User.objects.create_superuser(email='admin@example.com', username='admin', password='password')

        # Создаем объявления
        self.active_listing = Listing.objects.create(
            title='Active Listing',
            owner=self.owner,
            description='A test description',
            location='Berlin',
            address='123 Test St',
            property_type=PropertyTypeChoices.APARTMENT,
            price=500000,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

        self.deleted_listing = Listing.objects.create(
            title='Deleted Listing',
            owner=self.owner,
            description='A deleted listing',
            location='Berlin',
            address='124 Test St',
            property_type=PropertyTypeChoices.APARTMENT,
            price=600000,
            rooms=4,
            status=ListingStatusChoices.DELETED
        )

    def test_anonymous_user_access_to_active_listing(self):
        url = reverse('listing-detail', kwargs={'id': self.active_listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_user_access_to_deleted_listing(self):
        url = reverse('listing-detail', kwargs={'id': self.deleted_listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_access_to_own_active_listing(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('listing-detail', kwargs={'id': self.active_listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_access_to_own_deleted_listing(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('listing-detail', kwargs={'id': self.deleted_listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_access_to_another_users_active_listing(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('listing-detail', kwargs={'id': self.active_listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_access_to_another_users_deleted_listing(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('listing-detail', kwargs={'id': self.deleted_listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_access_to_any_listing(self):
        self.client.force_authenticate(user=self.admin)
        url_active = reverse('listing-detail', kwargs={'id': self.active_listing.id})
        url_deleted = reverse('listing-detail', kwargs={'id': self.deleted_listing.id})

        response_active = self.client.get(url_active)
        response_deleted = self.client.get(url_deleted)

        self.assertEqual(response_active.status_code, status.HTTP_200_OK)
        self.assertEqual(response_deleted.status_code, status.HTTP_200_OK)

    def test_access_to_nonexistent_listing(self):
        url = reverse('listing-detail', kwargs={'id': 9999})  # Несуществующий ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
