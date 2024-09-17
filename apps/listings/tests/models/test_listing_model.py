from time import sleep
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices
from apps.users.models import User


class ListingModelTest(TestCase):

    def setUp(self):
        self.business_user = User.objects.create_user(
            email='business@example.com',
            username='business_user',
            password='password123',
            is_business_account=True
        )

        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            username='regular_user',
            password='password123',
            is_business_account=False
        )

    def test_owner_is_required(self):
        listing = Listing(
            title='Test Listing Title',
            description='Test description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_owner_business_account_only(self):
        listing = Listing(
            owner=self.regular_user,
            title='Test Listing Title',
            description='Test description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

        listing = Listing(
            owner=self.business_user,
            title='Test Listing Title',
            description='Test description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        try:
            listing.full_clean()
        except ValidationError:
            self.fail("Listing creation failed for a business user.")

    def test_title_length(self):
        listing = Listing(
            owner=self.business_user,
            title='Short',
            description='Test description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_title_max_length(self):
        listing = Listing(
            owner=self.business_user,
            title='T' * 101,
            description='Test description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_description_max_length(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='D' * 501,
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_location_max_length(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='L' * 101,
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_property_type_default_value(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            price=100.00,
            rooms=2
        )
        listing.full_clean()
        self.assertEqual(listing.property_type, PropertyTypeChoices.OTHER)

    def test_price_min_value(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=0.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_rooms_min_value(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=0
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_status_default_value(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            price=100.00,
            rooms=2
        )
        listing.full_clean()
        self.assertEqual(listing.status, ListingStatusChoices.DRAFT)

    def test_soft_delete_method(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )
        listing.soft_delete()
        self.assertEqual(listing.status, ListingStatusChoices.DELETED)
        self.assertTrue(listing.status_changed_at <= timezone.now())

    def test_activate_method(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )
        listing.activate()
        self.assertEqual(listing.status, ListingStatusChoices.ACTIVE)
        self.assertTrue(listing.status_changed_at <= timezone.now())

    def test_deactivate_method(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )
        listing.deactivate()
        self.assertEqual(listing.status, ListingStatusChoices.DEACTIVATED)
        self.assertTrue(listing.status_changed_at <= timezone.now())

    def test_str_method(self):
        listing = Listing(
            owner=self.business_user,
            title='Test Listing Title',
            description='Test description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        self.assertEqual(str(listing), 'Test Listing Title')

    def test_address_max_length(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='A' * 101,
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_status_invalid_value(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=99
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_status_changed_at_updates_on_status_change(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )
        old_status_changed_at = listing.status_changed_at
        sleep(0.1)
        listing.activate()
        self.assertNotEqual(listing.status_changed_at, old_status_changed_at)

    def test_status_changed_at_set_on_creation(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        self.assertIsNotNone(listing.status_changed_at)

    def test_created_at_auto_now_add(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        self.assertIsNotNone(listing.created_at)
        self.assertTrue(listing.created_at <= timezone.now())

    def test_updated_at_auto_now(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        old_updated_at = listing.updated_at
        sleep(0.1)
        listing.title = 'Updated Title'
        listing.save()
        listing.refresh_from_db()
        self.assertNotEqual(listing.updated_at, old_updated_at)

    def test_change_status_updates_only_when_different(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )
        old_status_changed_at = listing.status_changed_at
        sleep(0.1)
        listing._change_status(ListingStatusChoices.DRAFT)
        self.assertEqual(listing.status_changed_at, old_status_changed_at)

    def test_change_status_updates_status_changed_at(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )
        old_status_changed_at = listing.status_changed_at
        sleep(0.1)
        listing._change_status(ListingStatusChoices.ACTIVE)
        self.assertNotEqual(listing.status_changed_at, old_status_changed_at)

    def test_change_status_uses_update_fields(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )
        listing._change_status(ListingStatusChoices.ACTIVE)
        self.assertEqual(listing.status, ListingStatusChoices.ACTIVE)

    def test_cascade_delete_on_owner_deletion(self):
        listing = Listing.objects.create(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=100.00,
            rooms=2
        )
        self.business_user.delete()
        with self.assertRaises(Listing.DoesNotExist):
            Listing.objects.get(id=listing.id)

    def test_database_queries_optimized_with_indexes(self):
        indexes = [index.fields for index in Listing._meta.indexes]
        expected_indexes = [['price'], ['location'], ['rooms'], ['status', 'created_at']]
        for expected in expected_indexes:
            self.assertIn(expected, indexes)

    def test_property_type_invalid_value(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type='invalid_type',
            price=100.00,
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_price_decimal_precision(self):
        listing = Listing(
            owner=self.business_user,
            title='Valid Title Here',
            description='Valid description',
            location='Test location',
            address='Test address',
            property_type=PropertyTypeChoices.HOUSE,
            price=Decimal('100.123'),
            rooms=2
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()
