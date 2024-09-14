from django.test import TestCase
from apps.users.models import User
from apps.users.serializers import CreateUserSerializer


class CreateUserSerializerTest(TestCase):
    def setUp(self):
        # Создаем пользователя для проверки уникальности (валидируется на уровне модели)
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )

    def test_create_user_success(self):
        # Данные для нового пользователя
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Проверка, что пользователь создан
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])
        self.assertTrue(user.check_password(data['password']))

    def test_passwords_do_not_match(self):
        # Проверка логики совпадения паролей
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'wrongpassword'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Passwords do not match.', serializer.errors['non_field_errors'])

    def test_missing_required_fields(self):
        # Отсутствуют обязательные поля
        data = {
            'username': '',
            'email': '',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)

    def test_invalid_email_format(self):
        # Неправильный формат email
        data = {
            'username': 'newuser',
            'email': 'not-an-email',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_password_validation(self):
        # Проверка минимальной длины пароля
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'short',
            'confirm_password': 'short'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_ignore_extra_fields(self):
        # Наличие дополнительных полей, не указанных в сериализаторе
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'extra_field': 'ignore this'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data)

    def test_password_is_hashed(self):
        # Проверка, что пароль хэшируется при сохранении
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Убедимся, что пароль не равен открытым данным
        self.assertNotEqual(user.password, 'newpassword123')
        self.assertTrue(user.check_password('newpassword123'))

    def test_max_length_fields(self):
        # Проверка максимальной длины полей
        data = {
            'username': 'u' * 151,  # Предполагаемая максимальная длина в модели - 150
            'email': 'e' * 244 + '@example.com',  # Длина email превышает стандарт
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)

    def test_case_insensitive_unique_username(self):
        # Проверка чувствительности к регистру для уникальности имени пользователя
        data = {
            'username': 'ExistingUser',  # Используем разный регистр для проверки
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this username already exists.', serializer.errors['username'])

    def test_case_insensitive_unique_email(self):
        # Проверка чувствительности к регистру для уникальности email
        data = {
            'username': 'newuser',
            'email': 'Existing@example.com',  # Используем разный регистр для проверки
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this email already exists.', serializer.errors['email'])

    def test_missing_confirm_password(self):
        # Проверка отсутствия поля confirm_password
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)

    def test_no_user_created_on_validation_failure(self):
        # Проверка, что пользователь не создается при ошибке валидации
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'wrongpassword'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(User.objects.count(), 1)  # Убедиться, что пользователь не создан

    def test_default_values_handling(self):
        # Проверка, что сериализатор правильно обрабатывает значения по умолчанию модели
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = CreateUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Предположим, что в модели User есть поле is_business_account по умолчанию False
        self.assertFalse(user.is_business_account)
