from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.serializers import ListingCreateSerializer
from apps.listings.choices import PropertyTypeChoices
from rest_framework.test import APIRequestFactory
from unittest.mock import Mock


class TestListingCreateSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )
        self.valid_data = {
            'title': 'Test Listing',
            'description': 'Test description',
            'location': 'Test Location',
            'address': '123 Test St',
            'property_type': PropertyTypeChoices.HOUSE,
            'price': '100.0',
            'rooms': 3
        }

        self.factory = APIRequestFactory()
        self.request = self.factory.post('/listings/create/')

    def test_required_fields(self):
        serializer = ListingCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        # Проверяем, что отсутствуют ошибки для обязательных полей
        required_fields = ['title', 'description', 'location', 'price', 'rooms']
        for field in required_fields:
            self.assertIn(field, serializer.errors)

    def test_field_validation(self):
        invalid_data = self.valid_data.copy()
        invalid_data['title'] = 'Short'  # Некорректная длина
        invalid_data['price'] = '-50'  # Отрицательное значение
        invalid_data['rooms'] = 0  # Недопустимое значение
        serializer = ListingCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('price', serializer.errors)
        self.assertIn('rooms', serializer.errors)

    def test_create_listing(self):
        self.request.user = self.user
        serializer = ListingCreateSerializer(data=self.valid_data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        self.assertEqual(listing.title, self.valid_data['title'])
        self.assertEqual(listing.owner, self.user)
        self.assertEqual(listing.price, float(self.valid_data['price']))

    def test_default_values_for_optional_fields(self):
        optional_data = self.valid_data.copy()
        optional_data.pop('property_type')

        self.request.user = self.user
        serializer = ListingCreateSerializer(data=optional_data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        self.assertEqual(listing.property_type, PropertyTypeChoices.OTHER)

    def test_invalid_field_data(self):
        invalid_data = self.valid_data.copy()
        invalid_data['price'] = 'invalid_number'
        serializer = ListingCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
