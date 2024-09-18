from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date, datetime
from unittest.mock import patch
from collections import defaultdict
from apps.bookings.choices import BookingStatusChoices
from apps.listings.choices import ListingStatusChoices
from apps.listings.models import Listing
from apps.bookings.models import Booking
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.listings.services import get_available_dates_by_month

User = get_user_model()


class GetAvailableDatesByMonthTest(TestCase):
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
        # Установка фиктивной сегодняшней даты
        self.today = datetime(2024, 2, 28).date()
        self.max_date = self.today + timedelta(days=90)

    def create_booking(self, start_offset, end_offset, status=BookingStatusChoices.CONFIRMED, user=None):
        """
        Вспомогательный метод для создания бронирований.
        start_offset и end_offset - смещения от фиктивной сегодняшней даты.
        """
        start_date = self.today + timedelta(days=start_offset)
        end_date = self.today + timedelta(days=end_offset)
        if not user:
            user = self.business_user
        try:
            booking = Booking.objects.create(
                listing=self.listing,
                user=user,
                start_date=start_date,
                end_date=end_date,
                total_price=100.00,
                status=status
            )
            return booking
        except ValidationError as e:
            self.fail(f"Создание бронирования не удалось: {e}")

    @patch('django.utils.timezone.now')
    def test_no_bookings(self, mock_now):
        """
        Проверка группировки доступных дат по месяцам при отсутствии бронирований.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        result = get_available_dates_by_month(self.listing)
        dates_by_month = defaultdict(list)
        for i in range(90):
            current_date = self.today + timedelta(days=i)
            month_key = current_date.strftime('%Y-%m')
            dates_by_month[month_key].append(current_date.strftime('%Y-%m-%d'))
        expected_result = [{'month': month, 'dates': sorted(dates)} for month, dates in dates_by_month.items()]
        expected_result.sort(key=lambda x: x['month'])
        self.assertEqual(result, expected_result, "Все даты должны быть доступны и правильно сгруппированы по месяцам.")

    @patch('django.utils.timezone.now')
    def test_single_booking_within_one_month(self, mock_now):
        """
        Проверка группировки доступных дат при наличии одного бронирования в пределах одного месяца.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования с дня 10 по 15
        self.create_booking(10, 15, status=BookingStatusChoices.CONFIRMED)
        result = get_available_dates_by_month(self.listing)
        excluded_dates = {self.today + timedelta(days=i) for i in range(10, 15)}
        all_available_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        dates_by_month = defaultdict(list)
        for date_obj in all_available_dates:
            month_key = date_obj.strftime('%Y-%m')
            dates_by_month[month_key].append(date_obj.strftime('%Y-%m-%d'))
        expected_result = [{'month': month, 'dates': sorted(dates)} for month, dates in dates_by_month.items()]
        expected_result.sort(key=lambda x: x['month'])
        self.assertEqual(result, expected_result, "Даты должны быть правильно сгруппированы по месяцам с исключенными бронированиями.")

    @patch('django.utils.timezone.now')
    def test_multiple_bookings_across_months(self, mock_now):
        """
        Проверка группировки доступных дат при наличии нескольких бронирований, охватывающих разные месяцы.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирований
        self.create_booking(10, 15, status=BookingStatusChoices.CONFIRMED)  # Месяц 1
        self.create_booking(30, 40, status=BookingStatusChoices.REQUEST)    # Месяц 2
        self.create_booking(60, 70, status=BookingStatusChoices.CONFIRMED)  # Месяц 3
        result = get_available_dates_by_month(self.listing)
        excluded_dates = {self.today + timedelta(days=i) for i in range(10, 15)} | \
                         {self.today + timedelta(days=i) for i in range(30, 40)} | \
                         {self.today + timedelta(days=i) for i in range(60, 70)}
        all_available_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        dates_by_month = defaultdict(list)
        for date_obj in all_available_dates:
            month_key = date_obj.strftime('%Y-%m')
            dates_by_month[month_key].append(date_obj.strftime('%Y-%m-%d'))
        expected_result = [{'month': month, 'dates': sorted(dates)} for month, dates in dates_by_month.items()]
        expected_result.sort(key=lambda x: x['month'])
        self.assertEqual(result, expected_result, "Даты должны быть правильно сгруппированы по месяцам с учетом нескольких бронирований.")

    @patch('django.utils.timezone.now')
    def test_spanning_booking_across_months(self, mock_now):
        """
        Проверка группировки доступных дат при наличии бронирования, охватывающего несколько месяцев.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования, охватывающего два месяца
        self.create_booking(28, 35, status=BookingStatusChoices.CONFIRMED)  # Охватывает конец текущего месяца и начало следующего
        result = get_available_dates_by_month(self.listing)
        excluded_dates = {self.today + timedelta(days=i) for i in range(28, 35)}
        all_available_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        dates_by_month = defaultdict(list)
        for date_obj in all_available_dates:
            month_key = date_obj.strftime('%Y-%m')
            dates_by_month[month_key].append(date_obj.strftime('%Y-%m-%d'))
        expected_result = [{'month': month, 'dates': sorted(dates)} for month, dates in dates_by_month.items()]
        expected_result.sort(key=lambda x: x['month'])
        self.assertEqual(result, expected_result, "Бронирование, охватывающее несколько месяцев, должно правильно исключать даты из соответствующих месяцев.")

    @patch('django.utils.timezone.now')
    def test_date_formatting(self, mock_now):
        """
        Проверка форматирования дат в строковом виде ('YYYY-MM-DD').
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования
        self.create_booking(10, 15, status=BookingStatusChoices.CONFIRMED)
        result = get_available_dates_by_month(self.listing)
        for entry in result:
            month = entry['month']
            for date_str in entry['dates']:
                # Проверка формата YYYY-MM-DD
                try:
                    parsed_date = date.fromisoformat(date_str)
                except ValueError:
                    self.fail(f"Дата {date_str} имеет некорректный формат. Ожидается 'YYYY-MM-DD'.")
                # Проверка соответствия месяца
                self.assertEqual(parsed_date.strftime('%Y-%m'), month, "Дата должна соответствовать своему месяцу.")

    @patch('django.utils.timezone.now')
    def test_leap_year_handling(self, mock_now):
        """
        Проверка корректной обработки високосного года.
        """
        # Установка фиктивной сегодняшней даты на 28 февраля 2024 года (високосный год)
        self.today = date(2024, 2, 28)
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Обновление даты в Listing, если необходимо
        self.listing.save()
        # Создание бронирования на 29 февраля и 1 марта
        self.create_booking(1, 3, status=BookingStatusChoices.CONFIRMED)  # 2024-02-29 и 2024-03-01
        result = get_available_dates_by_month(self.listing)
        excluded_dates = {date(2024, 2, 29), date(2024, 3, 0 + 1)}  # 2024-02-29
        all_available_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        dates_by_month = defaultdict(list)
        for date_obj in all_available_dates:
            month_key = date_obj.strftime('%Y-%m')
            dates_by_month[month_key].append(date_obj.strftime('%Y-%m-%d'))
        expected_result = [{'month': month, 'dates': sorted(dates)} for month, dates in dates_by_month.items()]
        expected_result.sort(key=lambda x: x['month'])
        self.assertEqual(result, expected_result, "Високосный год должен корректно обрабатываться, включая 29 февраля.")

    @patch('django.utils.timezone.now')
    def test_month_sorting(self, mock_now):
        """
        Проверка правильности сортировки месяцев в результате.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание нескольких бронирований для разных месяцев
        self.create_booking(10, 15, status=BookingStatusChoices.CONFIRMED)
        self.create_booking(30, 35, status=BookingStatusChoices.CONFIRMED)
        self.create_booking(60, 65, status=BookingStatusChoices.CONFIRMED)
        result = get_available_dates_by_month(self.listing)
        # Проверка сортировки месяцев
        months = [entry['month'] for entry in result]
        self.assertEqual(months, sorted(months), "Месяцы должны быть отсортированы в порядке возрастания.")

    @patch('django.utils.timezone.now')
    def test_partial_availability_in_months(self, mock_now):
        """
        Проверка корректности списка доступных дат при частичной доступности в месяцах.
        """
        mock_now.return_value = timezone.make_aware(datetime.combine(self.today, datetime.min.time()))
        # Создание бронирования в середине первого месяца
        self.create_booking(10, 15, status=BookingStatusChoices.CONFIRMED)
        result = get_available_dates_by_month(self.listing)
        excluded_dates = {self.today + timedelta(days=i) for i in range(10, 15)}
        all_available_dates = sorted({self.today + timedelta(days=i) for i in range(90)} - excluded_dates)
        dates_by_month = defaultdict(list)
        for date_obj in all_available_dates:
            month_key = date_obj.strftime('%Y-%m')
            dates_by_month[month_key].append(date_obj.strftime('%Y-%m-%d'))
        expected_result = [{'month': month, 'dates': sorted(dates)} for month, dates in dates_by_month.items()]
        expected_result.sort(key=lambda x: x['month'])
        self.assertEqual(result, expected_result, "Доступные даты должны корректно отображаться в месяцах с частичной доступностью.")
