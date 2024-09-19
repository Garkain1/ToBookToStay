from rest_framework import serializers
from ..models import Review
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices


class ReviewListSerializer(serializers.ModelSerializer):
    reviewer = serializers.ReadOnlyField(source='reviewer.username')
    reviewer_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'reviewer', 'reviewer_id']
        read_only_fields = ['id', 'rating', 'comment', 'reviewer', 'reviewer_id', 'listing_id',
                            'status', 'status_changed_at', 'created_at', 'updated_at']

    def to_representation(self, instance):
        # Получаем оригинальное представление
        data = super().to_representation(instance)

        # Добавляем дополнительные поля для администратора
        request = self.context.get('request')
        if request and request.user.is_staff:
            data['status'] = instance.status
            data['created_at'] = instance.created_at
            data['updated_at'] = instance.updated_at
            data['status_changed_at'] = instance.status_changed_at

        return data


class ReviewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'reviewer_id', 'listing_id']
        read_only_fields = ['id', 'rating', 'comment', 'reviewer', 'reviewer_id', 'listing_id',
                            'status', 'status_changed_at', 'created_at', 'updated_at']

    def to_representation(self, instance):
        # Получаем исходное представление данных
        representation = super().to_representation(instance)

        # Проверяем, является ли пользователь администратором
        request = self.context.get('request')
        if request and request.user.is_staff:
            # Добавляем дополнительные поля для администратора
            admin_fields = {
                'reviewer': instance.reviewer.username,
                'status': instance.status,
                'status_changed_at': instance.status_changed_at,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at,
            }
            representation.update(admin_fields)

        return representation


class ReviewCreateSerializer(serializers.ModelSerializer):
    reviewer_id = serializers.ReadOnlyField(source='reviewer.id')
    listing_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'reviewer_id', 'listing_id']  # Убрали поле 'id'
        extra_kwargs = {
            'rating': {'required': False},
            'comment': {'required': False}
        }

    def validate(self, data):
        user = self.context['request'].user
        listing = self.context['listing']

        # Проверка статуса листинга
        if listing.status != ListingStatusChoices.ACTIVE:
            raise serializers.ValidationError('Cannot review a listing that is not active.')

        # Проверка возможности оставить отзыв
        if not Review.can_user_review(user, listing):
            raise serializers.ValidationError('You can only review a listing if you have completed a booking for it and have not reviewed it yet.')

        return data

    def create(self, validated_data):
        validated_data['listing'] = self.context['listing']
        validated_data['reviewer'] = self.context['request'].user
        return Review.objects.create(**validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


class ReviewStatusActionSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=['apply_shadow_ban', 'soft_delete'], write_only=True)

    class Meta:
        model = Review
        fields = ['action']

    def update(self, instance, validated_data):
        action = validated_data.get('action')

        if action == 'apply_shadow_ban':
            instance.apply_shadow_ban()
        elif action == 'soft_delete':
            instance.soft_delete()

        instance.save()
        return instance
