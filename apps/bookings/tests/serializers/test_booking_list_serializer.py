from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingListSerializer
from apps.listings.models import Listing
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from django.utils import timezone
from datetime import timedelta


class TestBookingListSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.listing_owner = get_user_model().objects.create_user(
            username='listingowner',
            email='listingowner@example.com',
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
            owner=self.listing_owner,
            description='Test description',
            location='Test Location',
            address='123 Test St',
            property_type='house',
            price=100.0,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )
        # Используем динамические даты для создания бронирования
        today = timezone.now().date()
        start_date = today + timedelta(days=10)
        end_date = today + timedelta(days=20)
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=start_date,
            end_date=end_date,
            total_price=1000.0,
            status=BookingStatusChoices.CONFIRMED
        )
        self.factory = APIRequestFactory()

    def test_serialization_fields(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = BookingListSerializer(self.booking, context={'request': request})
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('listing_id', data)
        self.assertIn('listing_title', data)
        self.assertIn('user_id', data)
        self.assertIn('user_username', data)
        self.assertIn('status', data)
        self.assertIn('status_display', data)
        self.assertIn('status_changed_at', data)

    def test_read_only_fields(self):
        serializer = BookingListSerializer()
        for field in serializer.Meta.fields:
            self.assertTrue(serializer.fields[field].read_only)

    def test_to_representation_without_staff_user(self):
        request = self.factory.get('/')
        request.user = self.user
        serializer = BookingListSerializer(self.booking, context={'request': request})
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('listing_id', data)
        self.assertIn('listing_title', data)
        self.assertIn('status_display', data)
        self.assertIn('status_changed_at', data)
        self.assertNotIn('user_id', data)
        self.assertNotIn('user_username', data)

    def test_to_representation_with_listing_owner(self):
        request = self.factory.get('/')
        request.user = self.listing_owner
        serializer = BookingListSerializer(self.booking, context={'request': request})
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('user_id', data)
        self.assertIn('user_username', data)
        self.assertIn('status_display', data)
        self.assertIn('status_changed_at', data)
        self.assertNotIn('listing_id', data)
        self.assertNotIn('listing_title', data)

    def test_to_representation_with_staff_user(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = BookingListSerializer(self.booking, context={'request': request})
        data = serializer.data
        self.assertIn('status_display', data)

    def test_human_readable_status(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = BookingListSerializer(self.booking, context={'request': request})
        data = serializer.data
        self.assertEqual(data['status_display'], 'Confirmed')

    def test_empty_booking_list(self):
        serializer = BookingListSerializer([], many=True)
        data = serializer.data
        self.assertEqual(data, [])
