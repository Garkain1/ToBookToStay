from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserChangePageTests(TestCase):
    def setUp(self):
        # Создаем суперпользователя и логиним его
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass"
        )
        self.client.login(username="admin@example.com", password="adminpass")

    def test_user_change_data(self):
        """
        Тестируем возможность изменения данных пользователя через админку
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        old_password_hash = user.password
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': 'new_email@example.com',
            'username': 'newusername',
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Проверяем, что редирект случился после успешного изменения

        # Проверяем, что данные пользователя изменились
        user.refresh_from_db()
        self.assertEqual(user.email, 'new_email@example.com')
        self.assertEqual(user.username, 'newusername')
        self.assertEqual(user.password, old_password_hash)

    def test_user_change_required_fields(self):
        """
        Тестируем, что нельзя сохранить пользователя без обязательных полей
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': '',  # Пустое значение для email
            'username': '',  # Пустое значение для username
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)

        # Извлекаем форму из контекста ответа
        form = response.context['adminform'].form
        self.assertTrue(form.errors)  # Убедимся, что есть ошибки формы
        self.assertIn('email', form.errors)  # Проверяем наличие ошибки для поля email
        self.assertIn('username', form.errors)  # Проверяем наличие ошибки для поля username

    def test_user_change_duplicate_email(self):
        """
        Тестируем, что нельзя сохранить пользователя с дублирующимся email
        """
        User.objects.create_user(
            email="existing@example.com",
            username="existing_user",
            password="userpass"
        )
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': 'existing@example.com',  # Email уже существует
            'username': 'newusername',
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)

        # Проверяем, что форма вернулась с ошибкой дублирования email
        form = response.context['adminform'].form  # Извлекаем форму из контекста ответа
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)  # Проверяем, что ошибка связана с email

    def test_user_change_status(self):
        """
        Тестируем изменение статуса пользователя через админку
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass",
            status='0'  # Начальный статус - Pending
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': '1',  # Изменение статуса на 'active'
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Успешный редирект после изменения

        # Проверяем, что статус пользователя изменился
        user.refresh_from_db()
        self.assertEqual(user.status, '1')  # Статус должен быть 'active'

    def test_user_change_business_account_flag(self):
        """
        Тестируем изменение флага бизнес-аккаунта
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass",
            is_business_account=False
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'is_business_account': True,  # Меняем флаг на True
            'status': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Успешный редирект после изменения

        user.refresh_from_db()
        self.assertTrue(user.is_business_account)  # Проверяем, что флаг изменился на True

    def test_user_change_cancel(self):
        """
        Тестируем отмену изменений (закрытие без сохранения)
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': 'new_email@example.com',
            'username': 'newusername',
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status': user.status,
            'is_staff': user.is_staff
        }
        # Имитируем отмену изменений (не отправляем POST-запрос)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что данные пользователя не изменились
        user.refresh_from_db()
        self.assertEqual(user.email, 'user@example.com')  # Данные остались прежними
        self.assertEqual(user.username, 'user')  # Данные остались прежними

    def test_user_change_invalid_email_format(self):
        """
        Тестируем, что нельзя сохранить пользователя с недопустимым форматом email
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': 'invalid-email',  # Некорректный email
            'username': user.username,
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)

        form = response.context['adminform'].form
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)  # Проверяем наличие ошибки для email

    def test_user_cannot_change_status_to_deleted(self):
        """
        Тестируем, что нельзя изменить статус пользователя на 'Deleted' через форму
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass",
            status='0'  # Pending
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': '3',  # Пытаемся изменить статус на 'Deleted'
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)

        form = response.context['adminform'].form
        self.assertTrue(form.errors)
        self.assertIn('status_choice', form.errors)  # Проверяем наличие ошибки для статуса

    def test_password_mismatch(self):
        """
        Тестируем, что нельзя сохранить пользователя, если введены несовпадающие пароли
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': user.email,
            'username': user.username,
            'password1': 'newpassword123',
            'password2': 'differentpassword',  # Несовпадающие пароли
            'is_business_account': user.is_business_account,
            'status_choice': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)

        # Проверка, что происходит редирект (302)
        self.assertEqual(response.status_code, 302)

        # Если редирект произошел, убедимся, что данные не были сохранены
        user.refresh_from_db()
        self.assertFalse(user.check_password('newpassword123'))  # Пароль не должен быть изменен

    def test_user_password_change(self):
        """
        Тестируем изменение пароля через форму смены пароля в админке
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="oldpassword"
        )

        # Создаем новый пароль
        new_password = 'newpassword123'

        # URL страницы смены пароля для пользователя
        url = reverse('admin:auth_user_password_change', args=[user.id])

        # Данные для отправки в форму смены пароля
        data = {
            'password1': new_password,  # Новый пароль
            'password2': new_password,  # Подтверждение пароля
        }

        # Отправляем POST-запрос на смену пароля
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Проверяем, что был редирект

        # Обновляем данные пользователя и проверяем, что пароль успешно изменен
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))  # Проверяем, что новый пароль установлен

    def test_username_min_length_validation(self):
        """
        Тестируем, что имя пользователя должно быть минимум 3 символа
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="validusername",
            password="userpass"
        )
        url = reverse('admin:users_user_change', args=[user.id])
        data = {
            'email': user.email,
            'username': 'ab',  # Некорректное имя (менее 3 символов)
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': user.status,
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)

        form = response.context['adminform'].form
        self.assertTrue(form.errors)  # Проверяем, что есть ошибки
        self.assertIn('username', form.errors)  # Ошибка должна быть в поле username

    def test_user_soft_delete_via_is_soft_deleted(self):
        """
        Тестируем мягкое удаление пользователя через поле is_soft_deleted
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass",
            status='1'  # Начальный статус - Active
        )
        url = reverse('admin:users_user_change', args=[user.id])

        # Отправляем POST-запрос с установкой флага is_soft_deleted
        data = {
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': '1',  # Активный статус остается в форме
            'is_soft_deleted': True,  # Устанавливаем флаг мягкого удаления
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Проверяем, что произошел редирект

        # Обновляем пользователя и проверяем, что статус изменился на 'Deleted'
        user.refresh_from_db()
        self.assertEqual(user.status, '3')  # Статус должен быть 'Deleted'

    def test_user_restore_from_soft_delete(self):
        """
        Тестируем отмену мягкого удаления через поле is_soft_deleted
        """
        user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="userpass",
            status='3'  # Начальный статус - Deleted (мягко удален)
        )
        url = reverse('admin:users_user_change', args=[user.id])

        # Отправляем POST-запрос с отменой флага is_soft_deleted
        data = {
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'is_business_account': user.is_business_account,
            'status_choice': '0',
            'is_soft_deleted': False,  # Убираем флаг мягкого удаления
            'is_staff': user.is_staff
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Обновляем пользователя и проверяем, что статус восстановлен
        user.refresh_from_db()
        self.assertNotEqual(user.status, '3')  # Статус больше не должен быть 'Deleted'
