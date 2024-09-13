from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AdminTests(TestCase):
    def setUp(self):
        # Создание суперпользователя
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass"
        )
        self.client.login(username="admin@example.com", password="adminpass")

    def test_admin_page_accessible(self):
        """
        Тестируем доступ к странице админки
        """
        url = reverse('admin:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_change_page(self):
        """
        Проверяем доступность страницы редактирования пользователя
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_add_page(self):
        """
        Проверяем доступность страницы создания пользователя
        """
        url = reverse('admin:users_user_add')  # Это URL для создания нового пользователя в админке
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
