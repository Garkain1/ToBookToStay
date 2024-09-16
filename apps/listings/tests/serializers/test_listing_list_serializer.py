from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.listings.models import Listing
from apps.listings.serializers import ListingListSerializer
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices


class TestListingListSerializer(TestCase):

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
        serializer = ListingListSerializer(self.listing, context={'request': request})
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('price', data)
        self.assertIn('location', data)
        self.assertIn('rooms', data)
        self.assertIn('property_type', data)
        self.assertIn('owner', data)
        self.assertIn('status_display', data)

    def test_read_only_fields(self):
        serializer = ListingListSerializer()
        for field in serializer.Meta.fields:
            self.assertTrue(serializer.fields[field].read_only)

    def test_to_representation_without_staff_user(self):
        request = self.factory.get('/')
        request.user = self.user
        serializer = ListingListSerializer(self.listing, context={'request': request})
        data = serializer.data
        self.assertNotIn('status_display', data)

    def test_to_representation_with_staff_user(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = ListingListSerializer(self.listing, context={'request': request})
        data = serializer.data
        self.assertIn('status_display', data)

    def test_human_readable_status(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = ListingListSerializer(self.listing, context={'request': request})
        data = serializer.data
        self.assertEqual(data['status_display'], 'Active')

    def test_empty_listing_list(self):
        serializer = ListingListSerializer([], many=True)
        data = serializer.data
        self.assertEqual(data, [])
