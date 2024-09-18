from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class ListingAvailabilityTest(TestCase):
    def setUp(self):
        # Создание пользователей
        self.business_user = User.objects.create_user(
            email='business@example.com',
            username='business_user',
            password='password123',
            is_business_account=True
        )
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            username='regular_user',
            password='password123',
            is_business_account=False
        )
        # Создание объявления (Listing) с корректным статусом
        self.listing = Listing.objects.create(
            owner=self.business_user,
            title='Test Listing',
            description='A test listing',
            location='Test Location',
            address='123 Test Street',
            property_type='HOUSE',
            price=100.00,
            rooms=2,
            status=ListingStatusChoices.ACTIVE
        )
        self.today = timezone.now().date()
        self.max_date = self.today + timedelta(days=90)

    def create_booking(self, start_offset, end_offset, status=BookingStatusChoices.CONFIRMED, user=None):
        """
        Вспомогательный метод для создания бронирований.
        start_offset и end_offset - смещения от сегодняшней даты.
        """
        start_date = self.today + timedelta(days=start_offset)
        end_date = self.today + timedelta(days=end_offset)
        if not user:
            user = self.business_user
        return Booking.objects.create(
            listing=self.listing,
            user=user,
            start_date=start_date,
            end_date=end_date,
            total_price=100.00,
            status=status
        )

    def test_is_available_no_bookings(self):
        """
        Проверка доступности при отсутствии бронирований.
        """
        start_date = self.today + timedelta(days=10)
        end_date = self.today + timedelta(days=15)
        self.assertTrue(self.listing.is_available(start_date, end_date))

    def test_is_available_conflicted_confirmed_booking(self):
        """
        Проверка доступности при наличии CONFIRMED бронирования.
        """
        # Создание подтвержденного бронирования с дня 10 по 15
        booking = self.create_booking(10, 15)
        # Перекрывающиеся даты
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=12), self.today + timedelta(days=14)))
        # Смежные до
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=5), self.today + timedelta(days=10)))
        # Смежные после
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=15), self.today + timedelta(days=20)))
        # Точно совпадающие
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=10), self.today + timedelta(days=15)))

    def test_is_available_conflicted_request_booking(self):
        """
        Проверка доступности при наличии REQUEST бронирования.
        """
        # Создание запроса на бронирование с дня 20 по 25
        booking = self.create_booking(20, 25, status=BookingStatusChoices.REQUEST)
        # Перекрывающиеся даты
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=22), self.today + timedelta(days=24)))
        # Нек перекрывающиеся даты
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=25), self.today + timedelta(days=30)))

    def test_is_available_non_conflicting_other_status_bookings(self):
        """
        Проверка доступности при наличии бронирований с не блокирующими статусами.
        """
        # Создание бронирования со статусом CANCELED
        booking = self.create_booking(30, 35, status=BookingStatusChoices.CANCELED)
        # Перекрывающиеся даты должны быть доступны, так как статус не блокирующий
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=32), self.today + timedelta(days=34)))

    def test_is_available_spanning_multiple_bookings(self):
        """
        Проверка доступности при наличии нескольких перекрывающихся бронирований.
        """
        # Создание первого бронирования
        booking1 = self.create_booking(40, 45)
        # Проверка доступности перед созданием второго бронирования
        if self.listing.is_available(self.today + timedelta(days=43), self.today + timedelta(days=50)):
            booking2 = self.create_booking(43, 50)
        # Проверка доступности для перекрывающегося диапазона
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=44), self.today + timedelta(days=46)))
        # Проверка доступности вне бронирований
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=35), self.today + timedelta(days=40)))
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=50), self.today + timedelta(days=55)))

    def test_is_available_booking_exceeds_max_date(self):
        """
        Проверка доступности для бронирования, превышающего 90-дневный лимит.
        """
        # Создание бронирования, которое начинается до max_date и заканчивается после
        # Этот вызов должен вызвать исключение, так как конец бронирования выходит за предел 90 дней
        with self.assertRaises(ValidationError):
            self.create_booking(80, 95)

        # Даты до max_date должны быть доступны
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=80), self.today + timedelta(days=90)))

        # Даты, выходящие за max_date, должны быть недоступны
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=85), self.today + timedelta(days=95)))
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=90), self.today + timedelta(days=95)))

    def test_is_available_booking_ends_today(self):
        """
        Проверка доступности для бронирования, заканчивающегося сегодня и нового бронирования, начинающегося на день окончания.
        """
        # Создание бронирования с today по today +1 (end_date = today +1)
        booking = self.create_booking(0, 1)

        # Проверка доступности на тот же период (должно быть False)
        self.assertFalse(self.listing.is_available(self.today, self.today + timedelta(days=1)))

        # Проверка доступности, начинающейся сразу после существующего бронирования (должно быть True)
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=1), self.today + timedelta(days=2)))

    def test_is_available_booking_starts_on_max_date(self):
        """
        Проверка доступности для бронирования, начинающегося на max_date.
        """
        # Создание бронирования, начинающегося на max_date
        # Согласно логике, start_date <= max_date недоступно
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=90), self.today + timedelta(days=91)))

    def test_is_available_exclude_booking_id(self):
        """
        Проверка доступности при обновлении бронирования с исключением его ID.
        """
        # Создание бронирования с дня 50 по 55
        booking = self.create_booking(50, 55)
        # Проверка доступности в перекрывающемся диапазоне с исключением текущего бронирования
        self.assertTrue(self.listing.is_available(
            self.today + timedelta(days=52),
            self.today + timedelta(days=53),
            exclude_booking_id=booking.id
        ))

    def test_is_available_multiple_bookings_non_overlapping(self):
        """
        Проверка доступности при наличии нескольких несмежных бронирований.
        """
        # Создание нескольких несмежных бронирований
        self.create_booking(10, 15)
        self.create_booking(20, 25)
        self.create_booking(30, 35)
        # Проверка доступности между бронированиями
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=15), self.today + timedelta(days=20)))
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=25), self.today + timedelta(days=30)))
        self.assertTrue(self.listing.is_available(self.today + timedelta(days=35), self.today + timedelta(days=40)))

    def test_is_available_booking_exactly_max_window(self):
        """
        Проверка доступности для бронирования, точно соответствующего 90-дневному окну.
        """
        # Создание бронирования, которое занимает весь 90-дневный период
        booking = self.create_booking(0, 90)
        self.assertFalse(self.listing.is_available(self.today, self.max_date))
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=0), self.today + timedelta(days=90)))
        # Бронирование, начинающееся на max_date, должно быть недоступно
        self.assertFalse(self.listing.is_available(self.today + timedelta(days=90), self.today + timedelta(days=91)))
