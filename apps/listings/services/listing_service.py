from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from apps.bookings.choices import BookingStatusChoices


def get_available_dates(listing):
    today = timezone.now().date()
    max_date = today + timedelta(days=90)

    booked_bookings = listing.bookings.filter(
        status__in=[BookingStatusChoices.CONFIRMED, BookingStatusChoices.REQUEST],
        start_date__lt=max_date,
        end_date__gt=today,
    ).values_list('start_date', 'end_date')

    booked_dates = set()
    for start, end in booked_bookings:
        start = max(start, today)
        end = min(end, max_date)
        days = (end - start).days
        booked_dates.update(start + timedelta(days=i) for i in range(days))

    # Создаем полный набор дат и исключаем забронированные
    all_dates = set(today + timedelta(days=i) for i in range((max_date - today).days))
    available_dates = sorted(all_dates - booked_dates)

    return available_dates


def get_available_dates_by_month(listing):
    available_dates = get_available_dates(listing)
    dates_by_month = defaultdict(list)

    for date_obj in available_dates:
        month_key = date_obj.strftime('%Y-%m')
        dates_by_month[month_key].append(date_obj.strftime('%Y-%m-%d'))

    # Формируем список словарей
    result = []
    for month, dates in dates_by_month.items():
        result.append({'month': month, 'dates': dates})

    # Сортируем результат по месяцам
    result.sort(key=lambda x: x['month'])
    return result
