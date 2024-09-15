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
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("User with this username already exists.")
        return value

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_business_account = validated_data.get('is_business_account', instance.is_business_account)
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'is_business_account',
            'status', 'status_changed_at', 'created_at', 'last_login', 'is_staff'
        ]
        read_only_fields = ['id', 'status', 'status_changed_at', 'created_at', 'last_login', 'is_staff']

    def get_status(self, obj):
        return obj.get_status_display()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        is_owner = request and request.user == instance

        if not is_owner and not request.user.is_staff:
            representation.pop('email', None)
            representation.pop('is_business_account', None)
            representation.pop('status', None)
            representation.pop('status_changed_at', None)
            representation.pop('created_at', None)
            representation.pop('last_login', None)
            representation.pop('is_staff', None)

        if is_owner and instance.status == UserStatusChoices.DELETED:
            raise serializers.ValidationError("This account is deleted and cannot be accessed.")

        if not request.user.is_staff:
            representation.pop('is_staff', None)
            representation.pop('status_changed_at', None)
            representation.pop('created_at', None)
            representation.pop('last_login', None)

        return representation


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        user = self.context['request'].user

        if not user.is_staff:
            current_password = data.get('current_password')
            if not current_password:
                raise serializers.ValidationError("Current password is required for non-admin users.")
            if not user.check_password(current_password):
                raise serializers.ValidationError("Current password is incorrect.")

        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')
        if new_password != confirm_new_password:
            raise serializers.ValidationError("New passwords do not match.")

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

    def get_status(self, obj):
        return obj.get_status_display()


class ActivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

    def validate(self, data):
        request = self.context.get('request')

        if self.instance.status == UserStatusChoices.ACTIVE:
            raise ValidationError("This account is already active.")

        if request.user.is_staff:
            return data

        if self.instance.status == UserStatusChoices.DELETED:
            raise ValidationError("You cannot activate a deleted account.")

        return data

    def update(self, instance, validated_data):
        instance.status = UserStatusChoices.ACTIVE
        instance.save()
        return instance


class DeactivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

    def validate(self, data):
        request = self.context.get('request')

        if self.instance.status == UserStatusChoices.DEACTIVATED:
            raise ValidationError("This account is already deactivated.")

        if self.instance.status == UserStatusChoices.DELETED:
            raise ValidationError("Cannot deactivate a deleted account.")

        return data

    def update(self, instance, validated_data):
        instance.status = UserStatusChoices.DEACTIVATED
        instance.save()
        return instance


class DeleteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

    def validate(self, data):
        request = self.context.get('request')

        if self.instance.status == UserStatusChoices.DELETED:
            raise ValidationError("This account is already deleted.")

        return data

    def update(self, instance, validated_data):
        instance.status = UserStatusChoices.DELETED
        instance.save()
        return instance
