from django import forms
from .models import SubmitProof
from django.core.exceptions import ValidationError

class SubmitProofForm(forms.ModelForm):
    # Hidden fields for GPS
    live_latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    live_longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = SubmitProof
        fields = ['activity_type', 'proof_image', 'description', 'claimed_latitude', 'claimed_longitude']

        widgets = {
            'activity_type': forms.Select(attrs={'id': 'activity'}),
            'proof_image': forms.ClearableFileInput(attrs={'id': 'file'}),
            'description': forms.Textarea(attrs={'id': 'description', 'rows': 4}),
        }

    def clean_proof_image(self):
        file = self.cleaned_data.get('proof_image')
        if file:
            
            if file.size > 12 * 1024 * 1024:  
                raise ValidationError("File too large. Maximum size allowed is 12MB.")

            
            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if file.content_type not in allowed_types:
                raise ValidationError("Invalid file type. Only JPEG, PNG, or PDF files are allowed.")

        return file

