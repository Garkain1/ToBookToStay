from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserAdminCreateTests(TestCase):
    def setUp(self):
        # Создаем суперпользователя и логинимся
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass"
        )
        self.client.login(username="admin@example.com", password="adminpass")

        self.existing_user = User.objects.create_user(
            username="existinguser",
            email="existinguser@example.com",
            password="password123"
        )

    def test_create_user(self):
        """
        Проверяем создание нового пользователя через админку
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data, follow=True)

        # Проверяем, что произошло перенаправление на страницу редактирования
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "was added successfully")

        # Проверяем, что пользователь был создан
        new_user = User.objects.filter(email='newuser@example.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.username, 'newuser')
        self.assertTrue(new_user.check_password('P@ssw0rd12345'))  # Проверяем корректность пароля
        self.assertIsNotNone(new_user.created_at)
        self.assertIsNotNone(new_user.status_changed_at)

    def test_short_username(self):
        """
        Проверяем ошибку валидации при слишком коротком имени пользователя
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'ab',  # Короткое имя
            'email': 'newuser@example.com',
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at least 3 characters")

    def test_invalid_email(self):
        """
        Проверяем ошибку валидации при неправильном формате email
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'newuser',
            'email': 'invalid-email',  # Неверный email
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address")

    def test_common_password(self):
        """
        Проверяем ошибку валидации при слишком простом пароле
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password123',  # Простой пароль
            'password2': 'password123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is too common")

    def test_password_mismatch(self):
        """
        Проверяем ошибку валидации при несовпадении паролей
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'P@ssw0rd12345',
            'password2': 'differentpassword',  # Несовпадение паролей
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn’t match")

    def test_long_username(self):
        """
        Проверяем ошибку валидации при слишком длинном имени пользователя
        """
        url = reverse('admin:users_user_add')
        long_username = 'a' * 51  # Имя длиной 51 символ, что превышает лимит
        data = {
            'username': long_username,
            'email': 'newuser@example.com',
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 50 characters")

    def test_email_already_exists(self):
        """
        Проверяем ошибку валидации при попытке создать пользователя с уже существующим email
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'newuser',
            'email': 'existinguser@example.com',  # Email уже существует
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User with this Email already exists")

    def test_missing_username(self):
        """
        Проверяем ошибку валидации при отсутствии имени пользователя
        """
        url = reverse('admin:users_user_add')
        data = {
            'email': 'newuser@example.com',
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")  # Проверяем, что поле username обязательно

    def test_missing_email(self):
        """
        Проверяем ошибку валидации при отсутствии email
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'newuser',
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")  # Проверяем, что поле email обязательно

    def test_username_already_exists(self):
        """
        Проверяем ошибку валидации при попытке создать пользователя с уже существующим именем пользователя
        """
        url = reverse('admin:users_user_add')
        data = {
            'username': 'existinguser',  # Имя уже существует
            'email': 'newemail@example.com',
            'password1': 'P@ssw0rd12345',
            'password2': 'P@ssw0rd12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User with this Username already exists.")
