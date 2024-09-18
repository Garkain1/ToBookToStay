from django.test import TestCase
from django.urls import reverse
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices
from apps.users.models import User


class TestListingAdminActions(TestCase):
    def setUp(self):
        # Создание обычного пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=True  # Устанавливаем статус бизнес-аккаунта
        )

        # Создание суперпользователя для входа в админку
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )

        # Аутентификация в качестве суперпользователя
        self.client.login(username='admin@example.com', password='adminpass')

        # Создание тестовых объектов Listing
        self.listing1 = Listing.objects.create(
            title='Test Listing 1',
            owner=self.user,  # Устанавливаем владельца на обычного пользователя
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
            owner=self.user,  # Устанавливаем владельца на обычного пользователя
            description='Test description 2',
            location='Test location 2',
            address='Test address 2',
            property_type='apartment',
            price=200.0,
            rooms=3,
            status=ListingStatusChoices.DRAFT
        )

    def test_make_active_action(self):
        url = reverse('admin:listings_listing_changelist')
        data = {
            'action': 'make_active',  # Имя действия, зарегистрированного в админке
            '_selected_action': [self.listing1.pk, self.listing2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'ACTIVE'
        self.listing1.refresh_from_db()
        self.listing2.refresh_from_db()
        self.assertEqual(self.listing1.status, ListingStatusChoices.ACTIVE)
        self.assertEqual(self.listing2.status, ListingStatusChoices.ACTIVE)

    def test_make_deactivated_action(self):
        url = reverse('admin:listings_listing_changelist')
        data = {
            'action': 'make_deactivated',
            '_selected_action': [self.listing1.pk, self.listing2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'DEACTIVATED'
        self.listing1.refresh_from_db()
        self.listing2.refresh_from_db()
        self.assertEqual(self.listing1.status, ListingStatusChoices.DEACTIVATED)
        self.assertEqual(self.listing2.status, ListingStatusChoices.DEACTIVATED)

    def test_make_deleted_action(self):
        url = reverse('admin:listings_listing_changelist')
        data = {
            'action': 'make_deleted',
            '_selected_action': [self.listing1.pk, self.listing2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'DELETED'
        self.listing1.refresh_from_db()
        self.listing2.refresh_from_db()
        self.assertEqual(self.listing1.status, ListingStatusChoices.DELETED)
        self.assertEqual(self.listing2.status, ListingStatusChoices.DELETED)
