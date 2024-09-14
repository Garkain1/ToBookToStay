from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..models import User
from ..choices import UserStatusChoices


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
