from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserAdminActionTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass"
        )
        self.client.login(username="admin@example.com", password="adminpass")

        # Создание тестовых пользователей
        self.user_1 = User.objects.create_user(
            email="user1@example.com",
            username="user1",
            password="password123",
            status='0'  # Pending
        )
        self.user_2 = User.objects.create_user(
            email="user2@example.com",
            username="user2",
            password="password123",
            status='0'  # Pending
        )

    def test_make_active_action(self):
        """
        Тестируем действие make_active
        """
        url = reverse('admin:users_user_changelist')
        data = {
            'action': 'make_active',  # Действие, определенное в UserAdmin
            '_selected_action': [self.user_1.pk, self.user_2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'active'
        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_1.status, '1')  # Active
        self.assertEqual(self.user_2.status, '1')  # Active

    def test_make_deactivated_action(self):
        """
        Тестируем действие make_deactivated
        """
        url = reverse('admin:users_user_changelist')
        data = {
            'action': 'make_deactivated',  # Действие, определенное в UserAdmin
            '_selected_action': [self.user_1.pk, self.user_2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'deactivated'
        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_1.status, '2')  # Deactivated
        self.assertEqual(self.user_2.status, '2')  # Deactivated

    def test_make_deleted_action(self):
        """
        Тестируем действие make_deleted (Soft Delete)
        """
        url = reverse('admin:users_user_changelist')
        data = {
            'action': 'make_deleted',  # Действие make_deleted (Soft Delete)
            '_selected_action': [self.user_1.pk, self.user_2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'Deleted' (Soft Delete)
        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_1.status, '3')  # Deleted (Soft Delete)
        self.assertEqual(self.user_2.status, '3')  # Deleted (Soft Delete)

    def test_make_pending_action(self):
        """
        Тестируем действие make_pending
        """
        # Для теста изменим статус пользователей на 'Active'
        self.user_1.status = '1'  # Active
        self.user_2.status = '1'  # Active
        self.user_1.save()
        self.user_2.save()

        url = reverse('admin:users_user_changelist')
        data = {
            'action': 'make_pending',  # Действие make_pending
            '_selected_action': [self.user_1.pk, self.user_2.pk],
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что статус изменен на 'Pending'
        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_1.status, '0')  # Pending
        self.assertEqual(self.user_2.status, '0')  # Pending
