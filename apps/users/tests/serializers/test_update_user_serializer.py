from django.test import TestCase
from apps.users.models import User
from apps.users.serializers import UpdateUserSerializer


class UpdateUserSerializerTest(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            is_business_account=False
        )
        # Создаем другого пользователя для проверки уникальности
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )

    def test_update_user_success(self):
        # Проверка успешного обновления данных пользователя
        data = {
            'username': 'updateduser',
            'email': 'updateduser@example.com',
            'is_business_account': True
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверка обновленных полей
        self.assertEqual(updated_user.username, data['username'])
        self.assertEqual(updated_user.email, data['email'])
        self.assertTrue(updated_user.is_business_account)

    def test_unique_email_update(self):
        # Проверка на уникальность email при обновлении
        data = {
            'email': 'existing@example.com'  # Уже существует
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this email already exists.', serializer.errors['email'])

    def test_unique_username_update(self):
        # Проверка на уникальность username при обновлении
        data = {
            'username': 'existinguser'  # Уже существует
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this username already exists.', serializer.errors['username'])

    def test_no_changes_when_data_unchanged(self):
        # Проверка, что передача тех же значений не изменяет данные
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'is_business_account': False
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверка, что значения остались прежними
        self.assertEqual(updated_user.username, 'testuser')
        self.assertEqual(updated_user.email, 'testuser@example.com')
        self.assertFalse(updated_user.is_business_account)

    def test_update_only_provided_fields(self):
        # Проверка, что изменяются только переданные поля
        data = {
            'email': 'newemail@example.com'
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверка, что только email изменился
        self.assertEqual(updated_user.email, 'newemail@example.com')
        self.assertEqual(updated_user.username, 'testuser')  # Не изменилось
        self.assertFalse(updated_user.is_business_account)    # Не изменилось

    def test_ignore_extra_fields(self):
        # Проверка, что сериализатор игнорирует дополнительные неиспользуемые поля
        data = {
            'username': 'newusername',
            'extra_field': 'should be ignored'
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверка, что дополнительные поля игнорируются
        self.assertEqual(updated_user.username, 'newusername')
        self.assertNotIn('extra_field', serializer.validated_data)

    def test_ignore_system_fields(self):
        # Проверка, что системные поля (например, is_staff) игнорируются
        data = {
            'username': 'newusername',
            'is_staff': True
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Проверка, что системное поле is_staff не изменилось
        self.assertEqual(updated_user.username, 'newusername')
        self.assertFalse(updated_user.is_staff)  # Должно остаться False, так как его изменение не разрешено

    def test_case_insensitive_unique_username_update(self):
        # Попытка обновления username с разным регистром
        data = {
            'username': 'EXISTINGUSER'  # Имеется в базе как 'existinguser'
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this username already exists.', serializer.errors['username'])

    def test_case_insensitive_unique_email_update(self):
        # Попытка обновления email с разным регистром
        data = {
            'email': 'EXISTING@EXAMPLE.COM'  # Имеется в базе как 'existing@example.com'
        }
        serializer = UpdateUserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this email already exists.', serializer.errors['email'])
