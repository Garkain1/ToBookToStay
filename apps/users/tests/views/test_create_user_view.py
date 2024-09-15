from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class CreateUserViewTests(APITestCase):

    def setUp(self):
        self.url = reverse('user-register')
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }

    def test_successful_registration(self):
        # Успешная регистрация
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_registration_with_incomplete_data(self):
        # Регистрация с неполными данными
        incomplete_data = {'username': 'testuser'}
        response = self.client.post(self.url, incomplete_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_registration_with_invalid_email(self):
        # Регистрация с некорректным email
        invalid_email_data = self.user_data.copy()
        invalid_email_data['email'] = 'invalidemail'
        response = self.client.post(self.url, invalid_email_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_with_existing_email(self):
        # Регистрация с уже существующим email
        User.objects.create_user(username='existinguser', email=self.user_data['email'], password='testpassword123')
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
