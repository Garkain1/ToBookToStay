from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.choices.user_status import UserStatusChoices

User = get_user_model()


class UserDetailViewTests(APITestCase):

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
        self.pending_user = User.objects.create_user(
            username='pendinguser',
            email='pendinguser@example.com',
            password='password',
            status=UserStatusChoices.PENDING
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

    def test_get_own_profile(self):
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-detail', args=[self.active_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_other_user_profile_as_active_user(self):
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-detail', args=[self.pending_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_other_user_profile_as_admin(self):
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-detail', args=[self.pending_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_deleted_user_profile_as_non_admin(self):
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-detail', args=[self.deleted_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_deleted_user_profile_as_admin(self):
        self.authenticate_user('admin@example.com', 'adminpassword')
        url = reverse('user-detail', args=[str(self.deleted_user.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_with_pending_or_deactivated_status(self):
        self.authenticate_user('activeuser@example.com', 'password')
        url = reverse('user-detail', args=[self.deactivated_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_own_pending_or_deactivated_profile(self):
        self.authenticate_user('pendinguser@example.com', 'password')
        url = reverse('user-detail', args=[self.pending_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_deleted_user_cannot_access_own_profile(self):
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-detail', args=[self.deleted_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_user_cannot_access_others(self):
        self.authenticate_user('deleteduser@example.com', 'password')
        url = reverse('user-detail', args=[self.active_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_user_access(self):
        url = reverse('user-detail', args=[self.active_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
