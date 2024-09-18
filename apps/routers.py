from django.urls import include, path


urlpatterns = [
    path('', include('apps.users.urls')),
    path('', include('apps.listings.urls')),
    path('', include('apps.bookings.urls')),
]
