from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from ..choices import UserStatusChoices
from ..models import User


class UserAdminForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text=(
            "Raw passwords are not stored, so there is no way to see the user’s password."
        ),
    )

    status_choice = forms.ChoiceField(
        choices=[(key, value) for key, value in UserStatusChoices.choices if key != UserStatusChoices.DELETED],
        label="Status", required=False
    )
    is_soft_deleted = forms.BooleanField(label="Soft deleted", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            if self.instance.status in [UserStatusChoices.PENDING,
                                        UserStatusChoices.ACTIVE,
                                        UserStatusChoices.DEACTIVATED]:
                self.fields['status_choice'].initial = self.instance.status
            self.fields['is_soft_deleted'].initial = self.instance.status == UserStatusChoices.DELETED

    def clean(self):
        cleaned_data = super().clean()
        status_choice = cleaned_data.get("status_choice")
        is_soft_deleted = cleaned_data.get("is_soft_deleted")

        if is_soft_deleted:
            self.instance.status = UserStatusChoices.DELETED
        else:
            self.instance.status = status_choice

        return cleaned_data

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'is_business_account', 'status')