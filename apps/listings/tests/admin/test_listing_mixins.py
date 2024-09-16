from django.test import TestCase
from django.utils.html import strip_tags
from apps.listings.models import Listing
from apps.listings.mixins import StatusMixin, SoftDeleteMixin
from apps.listings.choices import ListingStatusChoices
from apps.users.models import User


class TestStatusMixin(TestCase, StatusMixin):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )

        # Создаем тестовый объект Listing
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,  # Указываем владельца
            description='Test description',
            location='Test location',
            address='Test address',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )

    def test_status_display_draft(self):
        self.listing.status = ListingStatusChoices.DRAFT
        self.assertIn('gray', self.status_display(self.listing))
        self.assertIn('Draft', strip_tags(self.status_display(self.listing)))

    def test_status_display_active(self):
        self.listing.status = ListingStatusChoices.ACTIVE
        self.assertIn('green', self.status_display(self.listing))
        self.assertIn('Active', strip_tags(self.status_display(self.listing)))

    def test_status_display_deactivated(self):
        self.listing.status = ListingStatusChoices.DEACTIVATED
        self.assertIn('red', self.status_display(self.listing))
        self.assertIn('Deactivated', strip_tags(self.status_display(self.listing)))

    def test_status_display_deleted(self):
        self.listing.status = ListingStatusChoices.DELETED
        self.assertEqual(self.status_display(self.listing), '-')


class TestSoftDeleteMixin(TestCase, SoftDeleteMixin):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )

        # Создаем тестовый объект Listing
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='Test location',
            address='Test address',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )

    def test_is_soft_deleted_true(self):
        # Устанавливаем статус DELETED и проверяем
        self.listing.status = ListingStatusChoices.DELETED
        self.assertTrue(self.is_soft_deleted(self.listing))

    def test_is_soft_deleted_false(self):
        # Устанавливаем статус отличным от DELETED и проверяем
        self.listing.status = ListingStatusChoices.ACTIVE
        self.assertFalse(self.is_soft_deleted(self.listing))
