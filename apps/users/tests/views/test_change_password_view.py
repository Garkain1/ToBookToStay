from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.choices.user_status import UserStatusChoices

User = get_user_model()


class ChangePasswordViewTests(APITestCase):

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
            password='oldpassword',
            status=UserStatusChoices.ACTIVE
        )

        self.deleted_user = User.objects.create_user(
            username='deleteduser',
            email='deleteduser@example.com',
            password='password',
            status=UserStatusChoices.DELETED
        )

        self.token_url = reverse('token_obtain_pair')
        self.change_password_url = reverse('user-change-password', args=[self.active_user.id])

    def authenticate_user(self, email, password):
        response = self.client.post(self.token_url, {'email': email, 'password': password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_successful_password_change(self):
        # Аутентифицированный пользователь меняет свой пароль
        self.authenticate_user('activeuser@example.com', 'oldpassword')
        url = reverse('user-change-password', args=[self.active_user.id])
        data = {
            'current_password': 'oldpassword',
            'new_password': 'NewComplexPassword123!',
            'confirm_new_password': 'NewComplexPassword123!'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_current_password(self):
        self.authenticate_user('activeuser@example.com', 'oldpassword')
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword',
            'confirm_new_password': 'newpassword'
        }
        response = self.client.put(self.change_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatched_new_passwords(self):
        self.authenticate_user('activeuser@example.com', 'oldpassword')
        data = {
            'current_password': 'oldpassword',
            'new_password': 'newpassword',
            'confirm_new_password': 'differentpassword'
        }
        response = self.client.put(self.change_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_as_admin_without_current_password(self):
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-change-password', args=[self.active_user.id])
        data = {
            'new_password': 'adminnewpassword',
            'confirm_new_password': 'adminnewpassword'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_deleted_user(self):
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-change-password', args=[self.deleted_user.id])
        data = {
            'current_password': 'password',
            'new_password': 'newpassword',
            'confirm_new_password': 'newpassword'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password_for_other_user_as_non_admin(self):
        self.authenticate_user('activeuser@example.com', 'oldpassword')
        url = reverse('user-change-password', args=[self.admin_user.id])
        data = {
            'current_password': 'oldpassword',
            'new_password': 'newpassword',
            'confirm_new_password': 'newpassword'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_user_change_password(self):
        # Неавторизованный пользователь пытается изменить пароль
        data = {
            'current_password': 'oldpassword',
            'new_password': 'newpassword',
            'confirm_new_password': 'newpassword'
        }
        response = self.client.put(self.change_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
