from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.choices.user_status import UserStatusChoices

User = get_user_model()


class ActivateUserViewTests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

        self.pending_user = User.objects.create_user(
            username='pendinguser',
            email='pendinguser@example.com',
            password='password',
            status=UserStatusChoices.PENDING
        )

        self.active_user = User.objects.create_user(
            username='activeuser',
            email='activeuser@example.com',
            password='password',
            status=UserStatusChoices.ACTIVE
        )

        self.deleted_user = User.objects.create_user(
            username='deleteduser',
            email='deleteduser@example.com',
            password='password',
            status=UserStatusChoices.DELETED
        )

        self.token_url = reverse('token_obtain_pair')

    def authenticate_user(self, email, password):
        response = self.client.post(self.token_url, {'email': email, 'password': password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_successful_activation_by_user(self):
        self.authenticate_user('pendinguser@example.com', 'password')
        url = reverse('user-activate', args=[self.pending_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.status, UserStatusChoices.ACTIVE)

    def test_successful_activation_by_admin(self):
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-activate', args=[self.pending_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.status, UserStatusChoices.ACTIVE)

    def test_activation_of_other_user_by_non_admin(self):
        self.authenticate_user('pendinguser@example.com', 'password')
        url = reverse('user-activate', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_activation_of_deleted_user(self):
        # Попытка активации аккаунта со статусом DELETED
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-activate', args=[self.deleted_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_of_already_active_user(self):
        # Попытка активации уже активного аккаунта
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-activate', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_user_activation(self):
        # Неавторизованный пользователь пытается активировать аккаунт
        url = reverse('user-activate', args=[self.pending_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_activation_of_deleted_user_by_admin(self):
        # Администратор активирует аккаунт пользователя со статусом DELETED
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-activate', args=[self.deleted_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.deleted_user.refresh_from_db()
        self.assertEqual(self.deleted_user.status, UserStatusChoices.ACTIVE)
