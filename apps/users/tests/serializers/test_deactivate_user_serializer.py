from django.test import TestCase
from apps.users.models import User
from apps.users.serializers import DeactivateUserSerializer
from apps.users.choices import UserStatusChoices
from rest_framework.test import APIRequestFactory


class DeactivateUserSerializerTest(TestCase):
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

    def test_successful_deactivation(self):
        # Проверка успешной деактивации активного аккаунта
        data = {'status': UserStatusChoices.DEACTIVATED}
        serializer = DeactivateUserSerializer(instance=self.user, data=data,
                                              context=self.get_serializer_context(self.user))
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверяем, что статус изменился на DEACTIVATED
        self.assertEqual(updated_user.status, UserStatusChoices.DEACTIVATED)

    def test_deactivation_of_already_deactivated_account(self):
        # Проверка деактивации уже деактивированного аккаунта
        self.user.status = UserStatusChoices.DEACTIVATED
        self.user.save()

        data = {'status': UserStatusChoices.DEACTIVATED}
        serializer = DeactivateUserSerializer(instance=self.user, data=data,
                                              context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_deactivation_of_deleted_account(self):
        # Проверка деактивации удаленного аккаунта
        self.user.status = UserStatusChoices.DELETED
        self.user.save()

        data = {'status': UserStatusChoices.DEACTIVATED}
        serializer = DeactivateUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_successful_deactivation_by_admin(self):
        # Проверка успешной деактивации аккаунта администратором
        data = {'status': UserStatusChoices.DEACTIVATED}
        serializer = DeactivateUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.admin_user))
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверяем, что статус изменился на DEACTIVATED
        self.assertEqual(updated_user.status, UserStatusChoices.DEACTIVATED)

    def test_invalid_status_and_no_status_change(self):
        # Устанавливаем начальный статус
        self.user.status = UserStatusChoices.ACTIVE
        self.user.save()

        # Передаем некорректный статус
        data = {'status': 'invalid_status'}
        serializer = DeactivateUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
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
            'status': UserStatusChoices.DEACTIVATED,
            'username': 'newusername',
            'email': 'newemail@example.com'
        }
        serializer = DeactivateUserSerializer(instance=self.user, data=data, context=self.get_serializer_context(self.user))
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверяем, что статус изменился
        self.assertEqual(updated_user.status, UserStatusChoices.DEACTIVATED)

        # Убедимся, что другие поля не изменились
        self.assertEqual(updated_user.username, original_username)
        self.assertEqual(updated_user.email, original_email)
