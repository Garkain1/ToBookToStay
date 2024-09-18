from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingUpdateSerializer
from apps.listings.models import Listing
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from django.utils import timezone
from datetime import timedelta


class TestBookingUpdateSerializer(TestCase):

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
            property_type=ListingStatusChoices.ACTIVE,
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
            status=BookingStatusChoices.CONFIRMED
        )

    def test_partial_update_fields(self):
        update_data = {'start_date': timezone.now().date() + timedelta(days=15)}
        serializer = BookingUpdateSerializer(self.booking, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.start_date, update_data['start_date'])
        self.assertEqual(updated_booking.end_date, self.booking.end_date)  # Убедимся, что другие поля не изменились

    def test_update_protected_fields(self):
        update_data = {
            'total_price': 2000.0,  # Поле, которое не должно обновляться через BookingUpdateSerializer
            'status': BookingStatusChoices.CANCELED  # Поле, которое также не должно обновляться напрямую
        }
        serializer = BookingUpdateSerializer(self.booking, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertNotEqual(updated_booking.total_price, 2000.0)  # Проверяем, что `total_price` не изменилось
        self.assertEqual(updated_booking.status, BookingStatusChoices.CONFIRMED)  # Проверяем, что `status` не изменился

    def test_partial_update_with_no_changes(self):
        update_data = {}
        serializer = BookingUpdateSerializer(self.booking, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.start_date, self.booking.start_date)  # Убедимся, что объект остался неизменным

    def test_update_existing_object(self):
        update_data = {'start_date': timezone.now().date() + timedelta(days=15)}
        serializer = BookingUpdateSerializer(self.booking, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.pk, self.booking.pk)  # Проверяем, что объект не изменил свой первичный ключ
        self.assertEqual(Booking.objects.count(), 1)  # Убедиться, что количество объектов не изменилось

    def test_update_immutable_fields(self):
        new_user = get_user_model().objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='password123'
        )
        new_listing = Listing.objects.create(
            title='New Test Listing',
            owner=new_user,
            description='New description',
            location='New Location',
            address='456 New St',
            property_type=ListingStatusChoices.ACTIVE,
            price=200.0,
            rooms=4,
            status=ListingStatusChoices.ACTIVE
        )
        update_data = {
            'user': new_user.id,
            'listing': new_listing.id
        }
        serializer = BookingUpdateSerializer(self.booking, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        # Проверяем, что 'user' не изменился
        self.assertEqual(updated_booking.user, self.user)

        # Проверяем, что 'listing' не изменился
        self.assertEqual(updated_booking.listing, self.listing)
