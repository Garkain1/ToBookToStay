from django.db import models


class ReviewStatusChoices(models.IntegerChoices):
    VISIBLE = 1, 'Visible'
    SHADOW_BANNED = 2, 'Shadow Banned'
    DELETED = 3, 'Deleted'


class ReviewStatusColors(models.IntegerChoices):
    GREEN = 1, 'green'
    RED = 2, 'red'
