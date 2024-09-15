from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.choices.user_status import UserStatusChoices

User = get_user_model()


class DeleteUserViewTests(APITestCase):

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

        self.pending_user = User.objects.create_user(
            username='pendinguser',
            email='pendinguser@example.com',
            password='password',
            status=UserStatusChoices.PENDING
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

    def test_successful_deletion_by_user(self):
        # Аутентифицированный пользователь удаляет свой аккаунт
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-delete', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.status, UserStatusChoices.DELETED)

    def test_successful_deletion_by_admin(self):
        # Администратор удаляет аккаунт другого пользователя
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-delete', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_already_deleted_user(self):
        # Попытка удаления уже удаленного аккаунта
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-delete', args=[self.deleted_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_user_deletion(self):
        # Неавторизованный пользователь пытается удалить аккаунт
        url = reverse('user-delete', args=[self.active_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deletion_of_other_user_by_non_admin(self):
        # Обычный пользователь пытается удалить аккаунт другого пользователя
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-delete', args=[self.deactivated_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deletion_of_deactivated_user(self):
        # Успешное удаление аккаунта со статусом DEACTIVATED
        self.authenticate_user('deactivateduser@example.com', 'password')
        url = reverse('user-delete', args=[self.deactivated_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.deactivated_user.refresh_from_db()
        self.assertEqual(self.deactivated_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_pending_user(self):
        # Успешное удаление аккаунта со статусом PENDING
        self.authenticate_user('pendinguser@example.com', 'password')
        url = reverse('user-delete', args=[self.pending_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_pending_user_by_admin(self):
        # Успешное удаление аккаунта со статусом PENDING администратором
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-delete', args=[self.pending_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_deactivated_user_by_admin(self):
        # Успешное удаление аккаунта со статусом DEACTIVATED администратором
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-delete', args=[self.deactivated_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.deactivated_user.refresh_from_db()
        self.assertEqual(self.deactivated_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_own_account_by_admin(self):
        # Администратор удаляет свой собственный аккаунт
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-delete', args=[self.admin_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_already_deleted_user_by_admin(self):
        # Администратор пытается удалить аккаунт, который уже имеет статус DELETED
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-delete', args=[self.deleted_user.id])
        response = self.client.put(url, {}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
