from django.test import TestCase
from apps.users.models import User
from apps.users.serializers import ChangePasswordSerializer
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request


class ChangePasswordSerializerTest(TestCase):
    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='oldpassword123'
        )
        self.factory = APIRequestFactory()

    def get_serializer_context(self, user):
        # Создаем запрос и устанавливаем пользователя
        request = self.factory.get('/')
        force_authenticate(request, user=user)  # Аутентифицируем пользователя
        return {'request': Request(request)}

    def test_successful_password_change(self):
        # Проверка успешного изменения пароля
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertTrue(serializer.is_valid())
        serializer.save()

        # Проверяем, что новый пароль установлен
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_incorrect_current_password(self):
        # Проверка ошибки при неверном текущем пароле
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_new_passwords_do_not_match(self):
        # Проверка ошибки при несовпадении новых паролей
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_new_password': 'differentpassword'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_password_validation(self):
        # Проверка валидации нового пароля (например, минимальной длины)
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'short',
            'confirm_new_password': 'short'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_missing_current_password(self):
        # Проверка ошибки при отсутствии текущего пароля
        data = {
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_missing_new_password(self):
        # Проверка ошибки при отсутствии нового пароля
        data = {
            'current_password': 'oldpassword123',
            'confirm_new_password': 'newpassword123'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_no_changes_if_passwords_match(self):
        # Проверка, что новый пароль не совпадает с текущим
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'oldpassword123',
            'confirm_new_password': 'oldpassword123'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('The new password cannot be the same as the current password.',
                      serializer.errors['non_field_errors'])

    def test_clear_data_after_save(self):
        # Проверка очистки данных после успешного сохранения
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        }
        serializer = ChangePasswordSerializer(data=data, context=self.get_serializer_context(self.user))
        self.assertTrue(serializer.is_valid())
        serializer.save()

        # Убедимся, что сериализатор не сохраняет пароли после изменения
        self.assertNotIn('current_password', serializer.validated_data)
        self.assertNotIn('new_password', serializer.validated_data)
