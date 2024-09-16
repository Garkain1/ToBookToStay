from django import forms
from ..choices import ListingStatusChoices
from ..models import Listing


class ListingAdminForm(forms.ModelForm):
    status_choice = forms.ChoiceField(
        choices=[
            (key, value) for key, value in ListingStatusChoices.choices
            if key != ListingStatusChoices.DELETED
        ],
        label="Status",
        required=False
    )
    is_soft_deleted = forms.BooleanField(label="Soft deleted", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['status_choice'].initial = self.instance.status
            self.fields['is_soft_deleted'].initial = self.instance.status == ListingStatusChoices.DELETED

    def clean(self):
        cleaned_data = super().clean()
        status_choice = cleaned_data.get("status_choice")
        is_soft_deleted = cleaned_data.get("is_soft_deleted")

        if is_soft_deleted:
            self.instance.status = ListingStatusChoices.DELETED
        else:
            self.instance.status = status_choice

        return cleaned_data

    class Meta:
        model = Listing
        fields = ('title', 'description', 'price', 'status_choice', 'is_soft_deleted')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
