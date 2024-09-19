from rest_framework import serializers
from django.core.exceptions import PermissionDenied
from apps.users.models import User
from apps.listings.models import Listing
from ..models import Booking


class BookingListSerializer(serializers.ModelSerializer):
    listing_title = serializers.ReadOnlyField(source='listing.title')
    user_id = serializers.ReadOnlyField(source='user.id')
    user_username = serializers.ReadOnlyField(source='user.username')  # Имя владельца бронирования
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'listing_id', 'listing_title', 'user_id', 'user_username', 'status',
            'status_display', 'status_changed_at'
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        # Ограничиваем отображаемые поля
        if not request.user.is_staff:
            if request.user == instance.user:
                public_fields = [
                    'id', 'listing_id', 'listing_title', 'status_display', 'status_changed_at'
                ]
                representation = {key: representation[key] for key in public_fields}
            elif request.user == instance.listing.owner:
                public_fields = [
                    'id', 'user_id', 'user_username', 'status_display', 'status_changed_at'
                ]
                representation = {key: representation[key] for key in public_fields}

        return representation


class BookingDetailSerializer(serializers.ModelSerializer):
    listing_title = serializers.ReadOnlyField(source='listing.title')
    user_id = serializers.ReadOnlyField(source='user.id')
    user_username = serializers.ReadOnlyField(source='user.username')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'listing_id', 'listing_title', 'user_id', 'user_username', 'start_date', 'end_date',
            'total_price', 'status', 'status_display', 'status_changed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')


        # Ограничиваем видимость полей для владельца бронирования
        if not request.user.is_staff:
            if request.user == instance.user:
                public_fields = [
                    'id', 'listing_id', 'listing_title', 'start_date', 'end_date', 'total_price',
                    'status_display', 'status_changed_at'
                ]
                representation = {key: representation[key] for key in public_fields}
            # Ограничиваем видимость полей для владельца листинга
            elif request.user == instance.listing.owner:
                public_fields = [
                    'id', 'user_id', 'user_username', 'start_date', 'end_date', 'total_price',
                    'status_display', 'status_changed_at'
                ]
                representation = {key: representation[key] for key in public_fields}

        return representation


class BookingCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )
    listing = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(),
        required=False  # Теперь делаем это поле необязательным
    )

    class Meta:
        model = Booking
        fields = ['listing', 'user', 'start_date', 'end_date']

    def validate(self, data):
        request = self.context['request']
        user = request.user

        # Получаем listing_id из URL и устанавливаем listing в данных
        listing_id = self.context['view'].kwargs.get('listing_id')
        if not listing_id:
            raise serializers.ValidationError("Listing ID is required.")

        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            raise serializers.ValidationError("Listing not found.")

        # Устанавливаем listing в данных
        data['listing'] = listing

        # Проверка доступности листинга для указанных дат
        if not listing.is_available(data['start_date'], data['end_date']):
            raise serializers.ValidationError('The selected dates are not available for this listing.')

        # Если пользователь не администратор, устанавливаем текущего пользователя
        if not user.is_staff:
            data['user'] = user
        else:
            # Если администратор, убедимся, что поле user присутствует
            if 'user' not in data or not data['user']:
                raise serializers.ValidationError("Admin must specify a user.")

        return data


class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date']

    def update(self, instance, validated_data):
        # Обновляем поля
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)

        instance.save()  # `save` вызывает `full_clean`, который содержит проверку доступности
        return instance


class BookingStatusActionSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=['request', 'confirm', 'complete', 'cancel', 'soft_delete'], write_only=True)

    class Meta:
        model = Booking
        fields = ['action']

    def update(self, instance, validated_data):
        action = self.context.get('view').action

        if action == 'request':
            instance.request()
        elif action == 'confirm':
            instance.confirm()
        elif action == 'complete':
            instance.complete()
        elif action == 'cancel':
            instance.cancel()
        elif action == 'soft_delete':
            instance.soft_delete()

        instance.save()
        return instance
