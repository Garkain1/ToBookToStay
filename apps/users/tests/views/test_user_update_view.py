from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.choices.user_status import UserStatusChoices

User = get_user_model()


class UserUpdateViewTests(APITestCase):

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

    def test_update_other_user_profile_as_non_admin(self):
        # Пользователь пытается обновить чужой профиль
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-update', args=[self.admin_user.id])
        data = {'username': 'newadmin'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_profile_as_deleted_user(self):
        # Пользователь со статусом DELETED пытается обновить свой профиль
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-update', args=[self.deleted_user.id])
        data = {'username': 'newdeleteduser'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_own_profile(self):
        # Частичное обновление профиля с использованием PATCH
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-update', args=[self.active_user.id])
        data = {'username': 'partialupdateuser'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'partialupdateuser')

    def test_unauthorized_user_update(self):
        # Неавторизованный пользователь пытается обновить профиль
        url = reverse('user-update', args=[self.active_user.id])
        data = {'username': 'hackerupdate'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_profile(self):
        # Аутентифицированный пользователь пытается обновить свой профиль
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-update', args=[self.active_user.id])
        data = {'username': 'newactiveuser', 'email': 'newactiveuser@example.com'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'newactiveuser')

    def test_update_other_user_profile_as_admin(self):
        # Администратор обновляет чужой профиль
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-update', args=[self.active_user.id])
        data = {'username': 'updatedactiveuser', 'email': 'updatedactiveuser@example.com'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'updatedactiveuser')

    def test_update_deleted_user_profile_as_admin(self):
        # Администратор обновляет профиль пользователя со статусом DELETED
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-update', args=[self.deleted_user.id])
        data = {'username': 'adminupdateddeleteduser', 'email': 'adminupdateddeleteduser@example.com'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'adminupdateddeleteduser')
