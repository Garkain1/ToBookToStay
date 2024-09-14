from django.test import TestCase
from apps.users.models import User
from apps.users.serializers import UserListSerializer
from apps.users.choices import UserStatusChoices


class UserListSerializerTest(TestCase):
    def setUp(self):
        # Создаем пользователей для тестирования
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
            status=UserStatusChoices.ACTIVE
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password456',
            status=UserStatusChoices.PENDING
        )

    def test_user_list_fields(self):
        # Проверка корректного вывода полей для одного пользователя
        serializer = UserListSerializer(instance=self.user1)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('username', data)
        self.assertIn('email', data)
        self.assertIn('status', data)
        self.assertNotIn('password', data)
        self.assertNotIn('is_staff', data)

    def test_status_display(self):
        # Проверка корректного отображения статуса
        serializer = UserListSerializer(instance=self.user1)
        data = serializer.data
        self.assertEqual(data['status'], self.user1.get_status_display())

        serializer = UserListSerializer(instance=self.user2)
        data = serializer.data
        self.assertEqual(data['status'], self.user2.get_status_display())

    def test_user_list_serialization(self):
        # Проверка корректной сериализации списка пользователей
        users = [self.user1, self.user2]
        serializer = UserListSerializer(instance=users, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['username'], 'user1')
        self.assertEqual(data[0]['status'], self.user1.get_status_display())
        self.assertEqual(data[1]['username'], 'user2')
        self.assertEqual(data[1]['status'], self.user2.get_status_display())
