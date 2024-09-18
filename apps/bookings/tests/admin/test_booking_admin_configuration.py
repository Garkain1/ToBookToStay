from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import Booking
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.users.models import User
from apps.bookings.admin import BookingAdmin


class TestBookingAdminConfiguration(TestCase):
    def setUp(self):
        # Создаем суперпользователя и логинимся
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin@example.com', password='adminpass')

        # Создаем пользователя и листинг
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='userpass',
            is_business_account=True
        )

        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='789 Oak St',
            address='789 Oak St',
            property_type='villa',
            price=150.0,
            rooms=4,
            status=ListingStatusChoices.DRAFT
        )

        # Создаем бронирование
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now().date() + timedelta(days=5),
            end_date=timezone.now().date() + timedelta(days=10),
            status=BookingStatusChoices.PENDING,
            total_price=750.0
        )

        self.site = AdminSite()
        self.admin = BookingAdmin(Booking, self.site)

    def test_list_display(self):
        """
        Проверяем, что все указанные поля присутствуют в list_display.
        """
        expected_display = (
            '__str__',
            'listing',
            'user',
            'start_date',
            'end_date',
            'status_display',
            'total_price',
            'is_soft_deleted',
            'created_at'
        )
        self.assertEqual(self.admin.list_display, expected_display)

    def test_list_filter(self):
        """
        Проверяем наличие фильтров в админке.
        """
        expected_filters = ('status', 'created_at', 'listing__owner')
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """
        Проверяем, что в админке установлены поля для поиска.
        """
        expected_search_fields = ('listing__title', 'user__username', 'listing__owner__username')
        self.assertEqual(self.admin.search_fields, expected_search_fields)

    def test_readonly_fields(self):
        """
        Проверяем, что указанные поля только для чтения.
        """
        expected_readonly_fields = ('total_price', 'status_changed_at', 'created_at', 'updated_at')
        self.assertEqual(self.admin.readonly_fields, expected_readonly_fields)

    def test_fieldsets(self):
        """
        Проверяем, что поля админки сгруппированы в соответствующие fieldsets.
        """
        expected_fieldsets = (
            (None, {'fields': ('listing', 'user', 'start_date', 'end_date')}),
            ('Price', {'fields': ('total_price',)}),
            ('Status', {'fields': ('status_choice', 'is_soft_deleted', 'status_changed_at')}),
            ('Metadata', {'fields': ('created_at', 'updated_at')}),
        )
        self.assertEqual(self.admin.fieldsets, expected_fieldsets)
