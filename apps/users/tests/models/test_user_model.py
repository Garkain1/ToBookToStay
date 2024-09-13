from django.test import TestCase
from django.utils import timezone
from apps.users.models import User
from apps.users.choices import UserStatusChoices


class UserModelTest(TestCase):

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpassword'
        )

    def test_create_user(self):
        # Проверяем, что пользователь был создан
        user_count = User.objects.count()
        self.assertEqual(user_count, 1)
        self.assertEqual(self.user.email, 'testuser@example.com')
        self.assertEqual(self.user.username, 'testuser')

    def test_unique_email(self):
        # Проверка уникальности email
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='testuser@example.com',  # Тот же email
                username='anotheruser',
                password='anotherpassword'
            )

    def test_unique_username(self):
        # Проверка уникальности username
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='anotheruser@example.com',
                username='testuser',  # Тот же username
                password='anotherpassword'
            )

    def test_status_change(self):
        # Изменяем статус пользователя
        self.user.status = UserStatusChoices.ACTIVE
        self.user.status_changed_at = timezone.now()
        self.user.save()

        self.assertEqual(self.user.status, UserStatusChoices.ACTIVE)

    def test_soft_delete(self):
        # Мягкое удаление пользователя
        self.user.status = UserStatusChoices.DELETED
        self.user.status_changed_at = timezone.now()
        self.user.save()

        self.assertEqual(self.user.status, UserStatusChoices.DELETED)
        self.assertTrue(self.user.status_changed_at)

    def test_full_delete(self):
        # Полное удаление пользователя
        user_id = self.user.id
        self.user.delete()

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)

    def test_create_superuser(self):
        # Создание суперпользователя
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='adminuser',
            password='adminpassword'
        )

        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class UserModelAdditionalTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser2@example.com',
            username='testuser2',
            password='testpassword'
        )

    def test_str_method(self):
        # Проверка метода __str__
        self.assertEqual(str(self.user), 'testuser2')

    def test_create_superuser_with_missing_fields(self):
        # Проверка, что при создании суперпользователя с некорректными полями возникает ошибка
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='superuser@example.com',
                username='superuser',
                password='superpassword',
                is_superuser=False  # Некорректное значение
            )

    def test_status_changed_at_auto_update(self):
        # Проверяем, что поле status_changed_at обновляется при изменении статуса
        old_status_changed_at = self.user.status_changed_at
        self.user.status = UserStatusChoices.ACTIVE
        self.user.save()

        self.assertNotEqual(self.user.status_changed_at, old_status_changed_at)

    def test_required_fields(self):
        # Проверка обязательности полей
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', username='testuser', password='testpassword')

        with self.assertRaises(ValueError):
            User.objects.create_user(email='testuser@example.com', username='', password='testpassword')

    def test_password_hashing(self):
        # Проверяем, что пароль хешируется
        raw_password = 'testpassword'
        self.assertTrue(self.user.check_password(raw_password))
