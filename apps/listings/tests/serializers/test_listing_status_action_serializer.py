from django.test import TestCase
from rest_framework.views import APIView
from unittest.mock import Mock
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
        mock_view = Mock(spec=APIView)
        mock_view.action = 'activate'
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'activate'},
                                                   context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.status, ListingStatusChoices.ACTIVE)

    def test_deactivate_action(self):
        self.listing.status = ListingStatusChoices.ACTIVE
        self.listing.save()

        mock_view = Mock(spec=APIView)
        mock_view.action = 'deactivate'
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'deactivate'},
                                                   context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.status, ListingStatusChoices.DEACTIVATED)

    def test_soft_delete_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'soft_delete'
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'soft_delete'},
                                                   context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.status, ListingStatusChoices.DELETED)

    def test_invalid_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'invalid_action'
        serializer = ListingStatusActionSerializer(self.listing, data={'action': 'invalid_action'},
                                                   context={'view': mock_view})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
