from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.listings.models import Listing
from apps.listings.serializers import ListingUpdateSerializer
from apps.listings.choices import PropertyTypeChoices, ListingStatusChoices


class TestListingUpdateSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.listing = Listing.objects.create(
            title='Initial Title',
            owner=self.user,
            description='Initial description',
            location='Initial Location',
            address='123 Initial St',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.0,
            rooms=3,
            status=ListingStatusChoices.DRAFT
        )

    def test_partial_update_fields(self):
        update_data = {'title': 'Updated Title'}
        serializer = ListingUpdateSerializer(self.listing, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.title, 'Updated Title')
        self.assertEqual(updated_listing.description, 'Initial description')  # Проверка, что другие поля не изменились

    def test_update_protected_fields(self):
        update_data = {
            'created_at': '2024-01-01T12:00:00Z',
            'status_changed_at': '2024-01-01T12:00:00Z',
            'status': ListingStatusChoices.ACTIVE
        }
        serializer = ListingUpdateSerializer(self.listing, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertNotEqual(updated_listing.created_at, '2024-01-01T12:00:00Z')
        self.assertNotEqual(updated_listing.status_changed_at, '2024-01-01T12:00:00Z')
        self.assertEqual(updated_listing.status, ListingStatusChoices.DRAFT)

    def test_update_immutable_fields(self):
        new_user = get_user_model().objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='password123'
        )
        update_data = {'owner': new_user.id}
        serializer = ListingUpdateSerializer(self.listing, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.owner, self.user)  # Проверяем, что владелец остался прежним

    def test_partial_update_with_no_changes(self):
        update_data = {}
        serializer = ListingUpdateSerializer(self.listing, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.title, 'Initial Title')  # Убедимся, что объект остался неизменным

    def test_update_existing_object(self):
        update_data = {'title': 'Updated Title'}
        serializer = ListingUpdateSerializer(self.listing, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_listing = serializer.save()
        self.assertEqual(updated_listing.pk, self.listing.pk)  # Проверяем, что объект не изменил свой первичный ключ
        self.assertEqual(Listing.objects.count(), 1)
