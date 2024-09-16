from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from apps.listings.admin import ListingAdmin
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices
from apps.users.models import User


class ListingAdminGeneralTests(TestCase):
    def setUp(self):
        # Создание суперпользователя
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin@example.com', password='adminpass')

        # Создаем обычного пользователя и объявления
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='userpass',
            is_business_account=True
        )

        self.listing1 = Listing.objects.create(
            title='Test Listing 1',
            owner=self.user,
            description='Test description 1',
            location='Test location 1',
            address='Test address 1',
            property_type='house',
            price=100.0,
            rooms=2,
            status=ListingStatusChoices.DRAFT
        )

        self.listing2 = Listing.objects.create(
            title='Test Listing 2',
            owner=self.user,
            description='Test description 2',
            location='Test location 2',
            address='Test address 2',
            property_type='apartment',
            price=200.0,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

    def test_listing_changelist_page(self):
        """
        Проверяем доступность страницы списка объявлений в админке.
        """
        url = reverse('admin:listings_listing_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_listing_add_page(self):
        """
        Проверяем доступность страницы добавления нового объявления в админке.
        """
        url = reverse('admin:listings_listing_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_listing_change_page(self):
        """
        Проверяем доступность страницы редактирования объявления в админке.
        """
        url = reverse('admin:listings_listing_change', args=[self.listing1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_filter_functionality(self):
        """
        Проверяем, что фильтры в админке работают корректно.
        """
        url = reverse('admin:listings_listing_changelist')

        # Применяем фильтр по статусу 'DRAFT'
        response = self.client.get(url, {'status': ListingStatusChoices.DRAFT})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Listing 1')
        self.assertNotContains(response, 'Test Listing 2')

        # Применяем фильтр по статусу 'ACTIVE'
        response = self.client.get(url, {'status': ListingStatusChoices.ACTIVE})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Listing 2')
        self.assertNotContains(response, 'Test Listing 1')

    def test_search_fields_functionality(self):
        """
        Проверяем, что поиск в админке работает корректно.
        """
        url = reverse('admin:listings_listing_changelist')

        # Поиск по названию
        response = self.client.get(url, {'q': 'Test Listing 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Listing 1')
        self.assertNotContains(response, 'Test Listing 2')

        # Поиск по описанию
        response = self.client.get(url, {'q': 'description 2'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Listing 2')
        self.assertNotContains(response, 'Test Listing 1')


class TestListingAdmin(TestCase):
    def setUp(self):
        # Создаем экземпляр пользователя и Listing
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True
        )

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

        self.site = AdminSite()
        self.admin = ListingAdmin(Listing, self.site)

    def test_list_display(self):
        # Проверяем, что все указанные поля присутствуют в list_display
        expected_display = ('title', 'owner', 'price', 'property_type', 'location', 'status_display', 'is_soft_deleted')
        self.assertEqual(self.admin.list_display, expected_display)

    def test_list_filter(self):
        # Проверяем наличие фильтров в админке
        expected_filters = (
        'status', 'location', 'rooms', 'property_type', 'status_changed_at', 'created_at', 'updated_at')
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_fieldsets(self):
        # Проверяем, что поля админки сгруппированы в соответствующие fieldsets
        expected_fieldsets = (
            (None, {'fields': ('title', 'description')}),
            ('Owner', {'fields': ('owner',)}),
            ('Listing Details', {'fields': ('price', 'rooms', 'property_type')}),
            ('Listing Location', {'fields': ('location', 'address')}),
            ('Status', {'fields': ('status_choice', 'is_soft_deleted', 'status_changed_at')}),
            ('Metadata', {'fields': ('created_at', 'updated_at')}),
        )
        self.assertEqual(self.admin.fieldsets, expected_fieldsets)

    def test_readonly_fields(self):
        # Проверяем, что указанные поля только для чтения
        expected_readonly_fields = ('status_changed_at', 'created_at', 'updated_at')
        self.assertEqual(self.admin.readonly_fields, expected_readonly_fields)

    def test_search_fields(self):
        # Проверяем, что в админке установлены поля для поиска
        expected_search_fields = ('title', 'description', 'owner__username', 'location', 'address')
        self.assertEqual(self.admin.search_fields, expected_search_fields)
