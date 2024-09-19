from django import forms
from ..choices import BookingStatusChoices
from ..models import Booking


class BookingAdminForm(forms.ModelForm):
    status_choice = forms.ChoiceField(
        choices=[
            (key, value) for key, value in BookingStatusChoices.choices
            if key != BookingStatusChoices.DELETED
        ],
        label="Status",
        required=False
    )
    is_soft_deleted = forms.BooleanField(label="Soft deleted", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['status_choice'].initial = self.instance.status
            self.fields['is_soft_deleted'].initial = self.instance.status == BookingStatusChoices.DELETED

    def clean(self):
        cleaned_data = super().clean()
        status_choice = cleaned_data.get("status_choice")
        is_soft_deleted = cleaned_data.get("is_soft_deleted")

        if is_soft_deleted:
            self.instance.status = BookingStatusChoices.DELETED
        else:
            self.instance.status = status_choice

        return cleaned_data

    class Meta:
        model = Booking
        fields = ('listing', 'user', 'start_date', 'end_date', 'total_price', 'status_choice', 'is_soft_deleted')
