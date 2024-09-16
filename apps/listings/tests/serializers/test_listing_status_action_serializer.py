from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.listings.models import Listing
from apps.listings.serializers import ListingStatusActionSerializer
from apps.listings.choices import ListingStatusChoices


class TestListingStatusActionSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='Test Location',
            address='123 Test St',
            property_type='house',
            price=100.0,
            rooms=3,
            status=ListingStatusChoices.DRAFT
        )

    def test_action_field_choices(self):
        serializer = ListingStatusActionSerializer()
        choices = serializer.fields['action'].choices
        self.assertIn('activate', choices)
        self.assertIn('deactivate', choices)
        self.assertIn('soft_delete', choices)

    def test_activate_action(self):
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'activate'})
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.status, ListingStatusChoices.ACTIVE)

    def test_deactivate_action(self):
        self.listing.status = ListingStatusChoices.ACTIVE
        self.listing.save()

        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'deactivate'})
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.status, ListingStatusChoices.DEACTIVATED)

    def test_soft_delete_action(self):
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'soft_delete'})
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.status, ListingStatusChoices.DELETED)

    def test_invalid_action(self):
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'invalid_action'})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
