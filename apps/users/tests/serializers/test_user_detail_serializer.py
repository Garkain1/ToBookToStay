from django.test import TestCase
from apps.users.models import User
from rest_framework.exceptions import ValidationError
from apps.users.serializers import UserDetailSerializer
from apps.users.choices import UserStatusChoices
from rest_framework.test import APIRequestFactory


class UserDetailSerializerTest(TestCase):
    def setUp(self):
        # Создаем обычного пользователя и администратора
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            status=UserStatusChoices.PENDING
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword'
        )
        self.deleted_user = User.objects.create_user(
            username='deleteduser',
            email='deleted@example.com',
            password='password123',
            status=UserStatusChoices.DELETED
        )
        self.factory = APIRequestFactory()

    def test_successful_user_detail(self):
        # Проверка успешного отображения информации о пользователе для владельца
        request = self.factory.get('/')
        request.user = self.user
        serializer = UserDetailSerializer(instance=self.user, context={'request': request})
        data = serializer.data

        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['status'], self.user.get_status_display())

    def test_admin_sees_all_fields(self):
        # Проверка, что администратор видит все поля
        request = self.factory.get('/')
        request.user = self.admin_user
        serializer = UserDetailSerializer(instance=self.user, context={'request': request})
        data = serializer.data

        self.assertIn('email', data)
        self.assertIn('is_business_account', data)
        self.assertIn('status', data)
        self.assertIn('status_changed_at', data)
        self.assertIn('created_at', data)
        self.assertIn('last_login', data)
        self.assertIn('is_staff', data)

    def test_non_owner_sees_limited_fields(self):
        # Проверка, что не владелец и не администратор видит ограниченное количество полей
        other_user = User.objects.create_user(username='otheruser', email='otheruser@example.com',
                                              password='password123')
        request = self.factory.get('/')
        request.user = other_user
        serializer = UserDetailSerializer(instance=self.user, context={'request': request})
        data = serializer.data

        self.assertNotIn('email', data)
        self.assertNotIn('is_business_account', data)
        self.assertNotIn('status', data)
        self.assertNotIn('status_changed_at', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('last_login', data)
        self.assertNotIn('is_staff', data)

    def test_owner_cannot_view_deleted_account(self):
        # Проверка, что владелец не может просматривать "удаленный" аккаунт
        request = self.factory.get('/')
        request.user = self.deleted_user
        serializer = UserDetailSerializer(instance=self.deleted_user, context={'request': request})

        with self.assertRaises(ValidationError):
            serializer.to_representation(self.deleted_user)

    def test_representation_for_different_statuses(self):
        # Проверка корректного отображения для разных статусов
        self.user.status = UserStatusChoices.ACTIVE
        self.user.save()

        request = self.factory.get('/')
        request.user = self.user
        serializer = UserDetailSerializer(instance=self.user, context={'request': request})
        data = serializer.data

        self.assertEqual(data['status'], self.user.get_status_display())
