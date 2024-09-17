from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Listing

User = get_user_model()


class ListingListSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Listing
        fields = ['id', 'title', 'price', 'location', 'rooms', 'property_type', 'owner', 'status_display']
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if not request or not request.user.is_staff:
            representation.pop('status_display', None)

        return representation


class ListingDetailSerializer(serializers.ModelSerializer):
    owner_id = serializers.ReadOnlyField(source='owner.id')
    owner = serializers.ReadOnlyField(source='owner.username')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'location', 'address',
            'rooms', 'property_type', 'status_display', 'status',
            'status_changed_at', 'created_at', 'updated_at', 'owner', 'owner_id'
        ]
        read_only_fields = fields  # Все поля делаются только для чтения

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if not request or (request.user != instance.owner and not request.user.is_staff):
            public_fields = [
                'id', 'title', 'description', 'price', 'location', 'address',
                'rooms', 'property_type', 'owner', 'owner_id'
            ]
            return {key: representation[key] for key in public_fields}

        if request.user == instance.owner:
            representation.pop('created_at', None)

        return representation


class ListingCreateSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),  # Позволяет выбрать любого пользователя
        required=False  # Делает поле необязательным
    )

    class Meta:
        model = Listing
        fields = ['title', 'description', 'price', 'rooms', 'location', 'address', 'property_type', 'owner']

    def validate_owner(self, value):
        if not value.is_business_account:
            raise serializers.ValidationError("Owner must be a business account.")
        return value

    def validate(self, data):
        user = self.context['request'].user

        # Если пользователь не администратор, игнорируем поле 'owner' и устанавливаем текущего пользователя
        if not user.is_staff:
            data['owner'] = user
        elif 'owner' not in data:
            # Если администратор не указал 'owner', устанавливаем текущего пользователя
            data['owner'] = user

        return data


class ListingUpdateSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )

    class Meta:
        model = Listing
        fields = ['title', 'description', 'location', 'address', 'property_type', 'price', 'rooms']

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance


class ListingStatusActionSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=['activate', 'deactivate', 'soft_delete'], write_only=True)

    class Meta:
        model = Listing
        fields = ['action']
        read_only_fields = ['status_changed_at', 'created_at', 'updated_at', 'owner']

    def update(self, instance, validated_data):
        action = self.context.get('view').action

        if action == 'activate':
            instance.activate()
        elif action == 'deactivate':
            instance.deactivate()
        elif action == 'soft_delete':
            instance.soft_delete()

        instance.save()
        return instance
