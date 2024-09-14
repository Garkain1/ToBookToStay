from django.test import TestCase
from apps.users.models import User
from apps.users.serializers import DeleteUserSerializer
from apps.users.choices import UserStatusChoices
from rest_framework.test import APIRequestFactory


class DeleteUserSerializerTest(TestCase):
    def setUp(self):
        # Создаем пользователей для тестирования
        self.user = User.objects.create_user(
            username='testuser',
            email='user@example.com',
            password='password123',
            status=UserStatusChoices.ACTIVE
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.factory = APIRequestFactory()

    def get_serializer_context(self, user):
        request = self.factory.get('/')
        request.user = user
        return {'request': request}

    def test_successful_deletion(self):
        # Проверка успешного удаления активного аккаунта
        data = {'status': UserStatusChoices.DELETED}
        serializer = DeleteUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверяем, что статус изменился на DELETED
        self.assertEqual(updated_user.status, UserStatusChoices.DELETED)

    def test_deletion_of_already_deleted_account(self):
        # Проверка удаления уже удаленного аккаунта
        self.user.status = UserStatusChoices.DELETED
        self.user.save()

        data = {'status': UserStatusChoices.DELETED}
        serializer = DeleteUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_successful_deletion_by_admin(self):
        # Проверка успешного удаления аккаунта администратором
        data = {'status': UserStatusChoices.DELETED}
        serializer = DeleteUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.admin_user))
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверяем, что статус изменился на DELETED
        self.assertEqual(updated_user.status, UserStatusChoices.DELETED)

    def test_invalid_status_and_no_status_change(self):
        # Устанавливаем начальный статус
        self.user.status = UserStatusChoices.ACTIVE
        self.user.save()

        # Передаем некорректный статус
        data = {'status': 'invalid_status'}
        serializer = DeleteUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())

        # Проверяем наличие ошибки
        self.assertIn('status', serializer.errors)
        self.assertIn('"invalid_status" is not a valid choice.', serializer.errors['status'][0])

        # Проверяем, что статус пользователя не изменился
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, UserStatusChoices.ACTIVE)

    def test_no_other_field_changes(self):
        # Устанавливаем начальный статус
        original_username = self.user.username
        original_email = self.user.email
        self.user.status = UserStatusChoices.ACTIVE
        self.user.save()

        # Передаем корректный статус и пытаемся изменить другие поля
        data = {
            'status': UserStatusChoices.DELETED,
            'username': 'newusername',
            'email': 'newemail@example.com'
        }
        serializer = DeleteUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверяем, что статус изменился
        self.assertEqual(updated_user.status, UserStatusChoices.DELETED)

        # Убедимся, что другие поля не изменились
        self.assertEqual(updated_user.username, original_username)
        self.assertEqual(updated_user.email, original_email)
