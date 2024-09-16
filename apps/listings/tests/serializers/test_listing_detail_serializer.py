from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.listings.models import Listing
from apps.listings.serializers import ListingDetailSerializer
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices


class TestListingDetailSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.admin_user = get_user_model().objects.create_user(
            username='adminuser',
            email='adminuser@example.com',
            password='password123',
            is_staff=True
        )
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='Test Location',
            address='123 Test St',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.0,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )
        self.factory = APIRequestFactory()

    def test_serialization_fields(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = ListingDetailSerializer(self.listing, context={'request': request})
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('description', data)
        self.assertIn('address', data)
        self.assertIn('status_changed_at', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_read_only_fields(self):
        serializer = ListingDetailSerializer()
        for field in serializer.Meta.fields:
            self.assertTrue(serializer.fields[field].read_only)

    def test_to_representation_public_fields(self):
        request = self.factory.get('/')
        request.user = get_user_model().objects.create_user(
            username='publicuser',
            email='publicuser@example.com',
            password='password123'
        )
        serializer = ListingDetailSerializer(self.listing, context={'request': request})
        data = serializer.data
        # Проверяем, что админские поля скрыты от обычного пользователя
        self.assertNotIn('created_at', data)
        self.assertNotIn('status_display', data)

    def test_to_representation_owner_user(self):
        request = self.factory.get('/')
        request.user = self.user  # Владелец листинга
        serializer = ListingDetailSerializer(self.listing, context={'request': request})
        data = serializer.data
        # Проверяем, что поле 'created_at' исключается для владельца
        self.assertNotIn('created_at', data)

    def test_to_representation_admin_user(self):
        request = self.factory.get('/')
        request.user = self.admin_user  # Администратор
        serializer = ListingDetailSerializer(self.listing, context={'request': request})
        data = serializer.data
        # Проверяем, что администратор видит все поля
        self.assertIn('created_at', data)
        self.assertIn('status_display', data)

    def test_human_readable_status(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = ListingDetailSerializer(self.listing, context={'request': request})
        data = serializer.data
        self.assertEqual(data['status_display'], 'Active')
