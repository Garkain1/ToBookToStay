from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..models import User
from ..choices import UserStatusChoices


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.pop('confirm_password', None)

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})

        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'is_business_account']

    def validate_email(self, value):
        # Проверка на уникальность email
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_username(self, value):
        # Проверка на уникальность username
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("User with this username already exists.")
        return value

    def update(self, instance, validated_data):
        # Обновляем поля пользователя
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_business_account = validated_data.get('is_business_account', instance.is_business_account)
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'is_business_account',
            'status', 'status_changed_at', 'created_at', 'last_login', 'is_staff'
        ]
        read_only_fields = ['id', 'status', 'status_changed_at', 'created_at', 'last_login', 'is_staff']

    def to_representation(self, instance):
        """Customize fields based on user permissions."""
        representation = super().to_representation(instance)
        request = self.context.get('request')

        # Определяем, является ли текущий пользователь владельцем
        is_owner = request and request.user == instance

        # Для других пользователей (не владелец и не администратор)
        if not is_owner and not request.user.is_staff:
            # Скрыть конфиденциальные поля
            representation.pop('email', None)
            representation.pop('is_business_account', None)
            representation.pop('status', None)
            representation.pop('status_changed_at', None)
            representation.pop('created_at', None)
            representation.pop('last_login', None)
            representation.pop('is_staff', None)

        # Для владельца, который не может видеть удаленные аккаунты
        if is_owner and instance.status == UserStatusChoices.DELETED:
            raise serializers.ValidationError("This account is deleted and cannot be accessed.")

        # Если пользователь не является администратором, скрываем админ-поля
        if not request.user.is_staff:
            representation.pop('is_staff', None)
            representation.pop('status_changed_at', None)
            representation.pop('created_at', None)
            representation.pop('last_login', None)

        return representation


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')

        # Проверка совпадения нового пароля и подтверждения
        if new_password != confirm_new_password:
            raise serializers.ValidationError("New passwords do not match.")

        # Валидация нового пароля
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})

        if new_password == data.get('current_password'):
            raise serializers.ValidationError("The new password cannot be the same as the current password.")

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        self.validated_data.pop('current_password', None)
        self.validated_data.pop('new_password', None)
        self.validated_data.pop('confirm_new_password', None)

        return user


class UserListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'status']


class ActivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']  # Будем изменять только статус

    def validate(self, data):
        request = self.context.get('request')  # Получаем пользователя из контекста запроса

        # Если аккаунт уже активен
        if self.instance.status == UserStatusChoices.ACTIVE:
            raise ValidationError("This account is already active.")

        # Если текущий пользователь - не администратор
        if not request.user.is_staff:
            # Разрешаем активацию только для статусов 'PENDING' или 'DEACTIVATED'
            if self.instance.status not in [UserStatusChoices.PENDING, UserStatusChoices.DEACTIVATED]:
                raise ValidationError("You can only activate an account with 'pending' or 'deactivated' status.")

        return data

    def update(self, instance, validated_data):
        # Устанавливаем статус "active"
        instance.status = UserStatusChoices.ACTIVE
        instance.save()
        return instance


class DeactivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

    def validate(self, data):
        request = self.context.get('request')

        # Если аккаунт уже деактивирован
        if self.instance.status == UserStatusChoices.DEACTIVATED:
            raise ValidationError("This account is already deactivated.")

        # Если текущий статус - "удален"
        if self.instance.status == UserStatusChoices.DELETED:
            raise ValidationError("Cannot deactivate a deleted account.")

        return data

    def update(self, instance, validated_data):
        # Устанавливаем статус "deactivated"
        instance.status = UserStatusChoices.DEACTIVATED
        instance.save()
        return instance


class DeleteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

    def validate(self, data):
        request = self.context.get('request')

        # Если аккаунт уже удален
        if self.instance.status == UserStatusChoices.DELETED:
            raise ValidationError("This account is already deleted.")

        return data

    def update(self, instance, validated_data):
        # Устанавливаем статус "deleted"
        instance.status = UserStatusChoices.DELETED
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                     style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                             style={'input_type': 'password'})
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=User.groups.field.related_model.objects.all(),
                                                required=False)
    user_permissions = serializers.PrimaryKeyRelatedField(many=True,
                                                          queryset=User.user_permissions.field.related_model.objects.all(),
                                                          required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'confirm_password', 'is_business_account', 'status',
            'status_changed_at', 'created_at', 'groups', 'user_permissions', 'is_staff', 'last_login'
        ]
        read_only_fields = ['status_changed_at', 'last_login', 'created_at']

    def to_representation(self, instance):
        """Customizes which fields are returned in the serialized data based on the user's permissions."""
        representation = super().to_representation(instance)
        request = self.context.get('request')

        # Hide 'is_staff' and 'status' for non-staff users
        if request and not request.user.is_staff:
            representation.pop('is_staff', None)
            representation.pop('status', None)
            representation.pop('status_changed_at', None)
            representation.pop('created_at', None)
            representation.pop('groups', None)
            representation.pop('user_permissions', None)
            representation.pop('last_login', None)

        if request and request.user != instance and not request.user.is_staff:
            representation.pop('is_business_account', None)

        return representation

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError("Username must be at most 50 characters long.")
        if not value.isalnum():
            raise serializers.ValidationError("Username must contain only letters and numbers.")

        if User.objects.filter(username=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A user with this username already exists.")

        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    @staticmethod
    def validate_status(value):
        if value not in dict(UserStatusChoices.choices):
            raise serializers.ValidationError("Invalid status.")
        return value

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.pop('confirm_password', None)

        if password:
            if password != confirm_password:
                raise serializers.ValidationError("Passwords do not match.")
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({"password": e.messages})

        if password and len(password) > 128:
            raise serializers.ValidationError("Password must be at most 128 characters long.")

        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])

        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])

        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)

        user.save()
        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
        return user
