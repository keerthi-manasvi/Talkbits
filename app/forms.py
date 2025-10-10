from django import forms
from .models import LANGUAGE_CHOICES, LanguageRegistration

class LanguageRegistrationForm(forms.ModelForm):
    # Hidden field to actually submit
    learning_language = forms.CharField(widget=forms.HiddenInput())
    # Dropdown for language they know
    known_language = forms.ChoiceField(choices=LANGUAGE_CHOICES, label="Language You Know")

    class Meta:
        model = LanguageRegistration
        fields = ['learning_language', 'known_language']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Optional: Disable dropdown of hidden field in template
        self.fields['learning_language'].required = True

    def clean_learning_language(self):
        learning_language = self.cleaned_data.get('learning_language')
        if self.user and LanguageRegistration.objects.filter(
            user=self.user, learning_language=learning_language
        ).exists():
            raise forms.ValidationError(f"You are already registered for {learning_language}.")
        return learning_language
