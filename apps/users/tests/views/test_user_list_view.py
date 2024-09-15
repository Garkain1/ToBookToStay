from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserListViewTests(APITestCase):

    def setUp(self):
        self.url = reverse('user-list')
        self.admin_user = User.objects.create_user(username='admin', email='admin@example.com', password='adminpassword')
        self.admin_user.is_staff = True
        self.admin_user.save()

        for i in range(15):
            User.objects.create_user(username=f'user{i}', email=f'user{i}@example.com', password='userpassword')

        self.token_url = reverse('token_obtain_pair')

    def authenticate_user(self, email, password):
        response = self.client.post(self.token_url, {'email': email, 'password': password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_access_user_list(self):
        self.authenticate_user('admin@example.com', 'adminpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_pagination_count(self):
        # Проверка общего количества пользователей
        self.authenticate_user('admin@example.com', 'adminpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 16)

    def test_pagination_page_size(self):
        # Проверка количества элементов на первой странице
        self.authenticate_user('admin@example.com', 'adminpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_pagination_next_page(self):
        # Проверка перехода на вторую страницу
        self.authenticate_user('admin@example.com', 'adminpassword')
        response = self.client.get(f'{self.url}?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

    def test_pagination_no_next_page(self):
        # Проверка отсутствия следующей страницы
        self.authenticate_user('admin@example.com', 'adminpassword')
        response = self.client.get(f'{self.url}?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['next'])
