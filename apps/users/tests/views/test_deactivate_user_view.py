from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.choices.user_status import UserStatusChoices

User = get_user_model()


class DeactivateUserViewTests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

        self.active_user = User.objects.create_user(
            username='activeuser',
            email='activeuser@example.com',
            password='password',
            status=UserStatusChoices.ACTIVE
        )

        self.deactivated_user = User.objects.create_user(
            username='deactivateduser',
            email='deactivateduser@example.com',
            password='password',
            status=UserStatusChoices.DEACTIVATED
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

    def test_successful_deactivation_by_user(self):
        # Аутентифицированный пользователь деактивирует свой аккаунт
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-deactivate', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.status, UserStatusChoices.DEACTIVATED)

    def test_successful_deactivation_by_admin(self):
        # Администратор деактивирует аккаунт другого пользователя
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-deactivate', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.status, UserStatusChoices.DEACTIVATED)

    def test_deactivation_of_already_deactivated_user(self):
        # Попытка деактивации уже деактивированного аккаунта
        self.authenticate_user('deactivateduser@example.com', 'password')
        url = reverse('user-deactivate', args=[self.deactivated_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivation_of_deleted_user(self):
        # Попытка деактивации аккаунта со статусом DELETED
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-deactivate', args=[self.deleted_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivation_of_deleted_user_by_admin(self):
        # Попытка деактивации аккаунта со статусом DELETED администратором
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-deactivate', args=[self.deleted_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_user_deactivation(self):
        # Неавторизованный пользователь пытается деактивировать аккаунт
        url = reverse('user-deactivate', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deactivation_of_other_user_by_non_admin(self):
        # Обычный пользователь пытается деактивировать аккаунт другого пользователя
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-deactivate', args=[self.deactivated_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
