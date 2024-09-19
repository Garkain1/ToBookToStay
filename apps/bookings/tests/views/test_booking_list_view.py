from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices, PropertyTypeChoices
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class TestOwnerListingBookingsListView(APITestCase):

    def setUp(self):
        # Создаем пользователей с различными ролями
        self.owner_user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password'
        )
        self.other_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )

        # Создаем листинг и бронирования
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.owner_user,
            description='A test description for the listing',
            location='Test City',
            address='123 Test St',
            property_type=PropertyTypeChoices.OTHER,
            price=100000.00,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )

        for i in range(15):
            Booking.objects.create(
                listing=self.listing,
                user=self.other_user,
                start_date=timezone.now() + timedelta(days=i + 1),
                end_date=timezone.now() + timedelta(days=i + 2),
                status=BookingStatusChoices.PENDING
            )

    def test_unauthenticated_user_access(self):
        response = self.client.get(reverse('owner-listing-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_owner_access(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(reverse('owner-listing-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Первая страница с пагинацией
        self.assertEqual(response.data['count'], 15)

    def test_authenticated_non_owner_access(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse('owner-listing-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('owner-listing-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Первая страница с пагинацией
        self.assertEqual(response.data['count'], 15)

    def test_pagination_second_page(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(reverse('owner-listing-bookings-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # На второй странице должно быть оставшихся 5 объектов
        self.assertEqual(len(response.data['results']), 5)

        def test_owner_cannot_see_deleted_bookings(self):
            # Создаем удаленное бронирование
            Booking.objects.create(
                listing=self.listing,
                user=self.other_user,
                start_date=timezone.now() + timedelta(days=20),
                end_date=timezone.now() + timedelta(days=25),
                status=BookingStatusChoices.DELETED
            )
            self.client.force_authenticate(user=self.owner_user)
            response = self.client.get(reverse('owner-listing-bookings-list'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Убедитесь, что удаленное бронирование не отображается
            self.assertEqual(response.data['count'], 15)  # Ожидается 15 активных бронирований

        def test_admin_can_see_deleted_bookings(self):
            # Создаем удаленное бронирование
            Booking.objects.create(
                listing=self.listing,
                user=self.other_user,
                start_date=timezone.now() + timedelta(days=20),
                end_date=timezone.now() + timedelta(days=25),
                status=BookingStatusChoices.DELETED
            )
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.get(reverse('owner-listing-bookings-list'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Убедитесь, что удаленное бронирование отображается
            self.assertEqual(response.data['count'], 16)


class TestListingBookingsListView(APITestCase):

    def setUp(self):
        # Создаем пользователей с различными ролями
        self.owner_user = User.objects.create_user(
            username='owneruser', email='owner@example.com', password='owner123', is_business_account=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser', email='regular@example.com', password='regular123'
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser', email='admin@example.com', password='admin123'
        )

        # Создаем листинг и бронирования
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.owner_user,
            description='Test description',
            location='Test City',
            address='123 Test St',
            property_type=PropertyTypeChoices.OTHER,
            price=500000,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

        for i in range(15):
            Booking.objects.create(
                listing=self.listing,
                user=self.regular_user,
                start_date=timezone.now() + timedelta(days=i),
                end_date=timezone.now() + timedelta(days=i + 1),
                status=BookingStatusChoices.PENDING
            )

    def test_unauthenticated_user_access(self):
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_owner_access(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Проверка пагинации
        self.assertEqual(response.data['count'], 15)

    def test_authenticated_non_owner_access(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Проверка пагинации
        self.assertEqual(response.data['count'], 15)

    def test_pagination_second_page(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_owner_cannot_see_deleted_bookings(self):
        # Создаем удаленное бронирование
        Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=timezone.now() + timedelta(days=20),
            end_date=timezone.now() + timedelta(days=25),
            status=BookingStatusChoices.DELETED
        )
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Убедитесь, что удаленное бронирование не отображается
        self.assertEqual(response.data['count'], 15)  # Ожидается 15 активных бронирований

    def test_admin_can_see_deleted_bookings(self):
        # Создаем удаленное бронирование
        Booking.objects.create(
            listing=self.listing,
            user=self.regular_user,
            start_date=timezone.now() + timedelta(days=20),
            end_date=timezone.now() + timedelta(days=25),
            status=BookingStatusChoices.DELETED
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('listing-bookings-list', kwargs={'listing_id': self.listing.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Убедитесь, что удаленное бронирование отображается
        self.assertEqual(response.data['count'], 16)


class TestUserBookingsListView(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(
            username='testuser', email='testuser@example.com', password='password123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', email='otheruser@example.com', password='password123'
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser', email='admin@example.com', password='admin123'
        )

        # Создаем листинг и бронирования
        self.listing = Listing.objects.create(
            title='Test Listing',
            owner=self.user,
            description='Test description',
            location='Test City',
            address='123 Test St',
            property_type=PropertyTypeChoices.OTHER,
            price=500000,
            rooms=3,
            status=ListingStatusChoices.ACTIVE
        )

        for i in range(15):
            Booking.objects.create(
                listing=self.listing,
                user=self.user,
                start_date=timezone.now() + timedelta(days=i),
                end_date=timezone.now() + timedelta(days=i + 1),
                status=BookingStatusChoices.PENDING
            )

    def test_unauthenticated_user_access(self):
        response = self.client.get(reverse('user-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Проверка пагинации
        self.assertEqual(response.data['count'], 15)  # Убедитесь, что пользователь видит свои бронирования

    def test_pagination_second_page(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-bookings-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # Остаток на второй странице

    def test_other_user_no_access_to_user_bookings(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse('user-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # Другой пользователь не видит чужие бронирования

    def test_admin_access(self):
        # Создаем бронирование для администратора
        admin_booking = Booking.objects.create(
            listing=self.listing,
            user=self.admin_user,
            start_date=timezone.now() + timedelta(days=20),
            end_date=timezone.now() + timedelta(days=21),
            status=BookingStatusChoices.PENDING
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('user-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Администратор видит только свои бронирования
        self.assertEqual(response.data['results'][0]['id'], admin_booking.id)

    def test_user_cannot_see_deleted_bookings(self):
        # Создаем удаленное бронирование
        Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=timezone.now() + timedelta(days=20),
            end_date=timezone.now() + timedelta(days=25),
            status=BookingStatusChoices.DELETED
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Убедитесь, что удаленное бронирование не отображается
        self.assertEqual(response.data['count'], 15)  # Ожидается 15 активных бронирований

    def test_admin_can_see_deleted_bookings_in_user_list(self):
        # Создаем удаленное бронирование для администратора
        Booking.objects.create(
            listing=self.listing,
            user=self.admin_user,
            start_date=timezone.now() + timedelta(days=20),
            end_date=timezone.now() + timedelta(days=25),
            status=BookingStatusChoices.DELETED
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('user-bookings-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Убедитесь, что удаленное бронирование отображается
        self.assertEqual(response.data['count'], 1)
