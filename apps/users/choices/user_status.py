from common.utils.doc_config import doc_language
from common.utils.localized_docs import localized_docstring
from django.db import models


class UserStatusChoices(models.TextChoices):
    PENDING = '0', 'Pending'
    ACTIVE = '1', 'Active'
    DEACTIVATED = '2', 'Deactivated'
    DELETED = '3', 'Deleted'
