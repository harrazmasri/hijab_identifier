from django import forms
from .models import ImageMedia

class ImageMediaForm (forms.ModelForm):
    class Meta:
        model = ImageMedia
        fields = [
            'filename',
            'extension',
            'file',
        ]