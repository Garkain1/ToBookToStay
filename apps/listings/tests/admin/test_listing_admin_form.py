from django.test import TestCase
from apps.listings.forms import ListingAdminForm
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices
from apps.users.models import User


class TestListingAdminForm(TestCase):
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

    def test_form_initial_values(self):
        form = ListingAdminForm(instance=self.listing)
        self.assertEqual(form.fields['status_choice'].initial, self.listing.status)
        self.assertFalse(form.fields['is_soft_deleted'].initial)

        # Устанавливаем статус DELETED и проверяем начальные значения
        self.listing.status = ListingStatusChoices.DELETED
        form = ListingAdminForm(instance=self.listing)
        self.assertTrue(form.fields['is_soft_deleted'].initial)

    def test_clean_status_choice(self):
        # Тестируем изменение статуса через форму
        form_data = {
            'title': 'Updated Test Listing',
            'description': 'Updated description',
            'price': 150.0,
            'status_choice': ListingStatusChoices.ACTIVE,
            'is_soft_deleted': False
        }
        form = ListingAdminForm(data=form_data, instance=self.listing)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['status_choice'], str(ListingStatusChoices.ACTIVE))
        self.assertEqual(self.listing.status, str(ListingStatusChoices.ACTIVE))

        # Тестируем установку статуса DELETED
        form_data['is_soft_deleted'] = True
        form = ListingAdminForm(data=form_data, instance=self.listing)
        self.assertTrue(form.is_valid())
        form.clean()
        self.assertEqual(self.listing.status, ListingStatusChoices.DELETED)

    def test_form_invalid_status_choice(self):
        form_data = {
            'title': 'Invalid Status Listing',
            'description': 'Invalid description',
            'price': 200.0,
            'status_choice': 999,  # Недопустимое значение
            'is_soft_deleted': False
        }
        form = ListingAdminForm(data=form_data, instance=self.listing)
        self.assertFalse(form.is_valid())
        self.assertIn('status_choice', form.errors)

    def test_widgets_configuration(self):
        form = ListingAdminForm(instance=self.listing)
        description_field = form.fields['description']
        self.assertEqual(description_field.widget.__class__.__name__, 'Textarea')
        self.assertEqual(description_field.widget.attrs['rows'], 4)
