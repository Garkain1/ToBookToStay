from decimal import Decimal
from rest_framework import serializers
from ..models import Listing


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

    class Meta:
        model = Listing
        fields = ['title', 'description', 'location', 'address', 'property_type', 'price', 'rooms']


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
        action = validated_data.get('action')

        if action == 'activate':
            instance.activate()
        elif action == 'deactivate':
            instance.deactivate()
        elif action == 'soft_delete':
            instance.soft_delete()

        instance.save()
        return instance
