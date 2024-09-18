from django.test import TestCase
from rest_framework.views import APIView
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingStatusActionSerializer
from apps.listings.models import Listing
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from django.utils import timezone
from datetime import timedelta

class TestBookingStatusActionSerializer(TestCase):

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
            status=ListingStatusChoices.ACTIVE
        )
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=20),
            total_price=1000.0,
            status=BookingStatusChoices.PENDING
        )

    def test_action_field_choices(self):
        serializer = BookingStatusActionSerializer()
        choices = serializer.fields['action'].choices
        self.assertIn('request', choices)
        self.assertIn('confirm', choices)
        self.assertIn('complete', choices)
        self.assertIn('cancel', choices)
        self.assertIn('soft_delete', choices)

    def test_request_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'request'
        serializer = BookingStatusActionSerializer(self.booking, data={'action': 'request'}, context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.status, BookingStatusChoices.REQUEST)

    def test_confirm_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'confirm'
        serializer = BookingStatusActionSerializer(self.booking, data={'action': 'confirm'}, context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.status, BookingStatusChoices.CONFIRMED)

    def test_complete_action(self):
        self.booking.status = BookingStatusChoices.CONFIRMED
        self.booking.save()

        mock_view = Mock(spec=APIView)
        mock_view.action = 'complete'
        serializer = BookingStatusActionSerializer(self.booking, data={'action': 'complete'}, context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.status, BookingStatusChoices.COMPLETED)

    def test_cancel_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'cancel'
        serializer = BookingStatusActionSerializer(self.booking, data={'action': 'cancel'}, context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.status, BookingStatusChoices.CANCELED)

    def test_soft_delete_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'soft_delete'
        serializer = BookingStatusActionSerializer(self.booking, data={'action': 'soft_delete'}, context={'view': mock_view})
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.status, BookingStatusChoices.DELETED)

    def test_invalid_action(self):
        mock_view = Mock(spec=APIView)
        mock_view.action = 'invalid_action'
        serializer = BookingStatusActionSerializer(self.booking, data={'action': 'invalid_action'}, context={'view': mock_view})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
