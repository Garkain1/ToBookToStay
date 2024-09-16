from django.db import models


class PropertyTypeChoices(models.TextChoices):
    HOUSE = 'house', 'House'
    APARTMENT = 'apartment', 'Apartment'
    CONDO = 'condo', 'Condominium'
    OTHER = 'other', 'Other'

    @classmethod
    def ordered_choices(cls):
        return [
            (cls.OTHER, cls.OTHER.label),
            (cls.HOUSE, cls.HOUSE.label),
            (cls.APARTMENT, cls.APARTMENT.label),
            (cls.CONDO, cls.CONDO.label),
        ]
