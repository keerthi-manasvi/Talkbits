from django import forms
from .models import LANGUAGE_CHOICES, LanguageRegistration

class LanguageRegistrationForm(forms.ModelForm):
    # Hidden field to actually submit
    learning_language = forms.CharField(widget=forms.HiddenInput())
    # Dropdown for language they know
    known_language = forms.ChoiceField(choices=[], label="Language You Know")

    class Meta:
        model = LanguageRegistration
        fields = ['learning_language', 'known_language']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Optional: Disable dropdown of hidden field in template
        self.fields['learning_language'].required = True
        learning_lang_val = None
        if self.is_bound:
            learning_lang_val = self.data.get(self.add_prefix('learning_language'))
        else:
            learning_lang_val = self.initial.get('learning_language') or (self.instance.learning_language if self.instance.pk else None)

        # removing the learning language from the dropdown choices
        if learning_lang_val:
            self.fields['known_language'].choices = [
                (code, name) for code, name in LANGUAGE_CHOICES if code != learning_lang_val
            ]
        else:
            self.fields['known_language'].choices = LANGUAGE_CHOICES

    def clean_learning_language(self):
        learning_language = self.cleaned_data.get('learning_language')
        if self.user and LanguageRegistration.objects.filter(
            user=self.user, learning_language=learning_language
        ).exists():
            raise forms.ValidationError(f"You are already registered for {learning_language}.")
        return learning_language
    
    def clean(self):
        """Cross-field validation to ensure they aren't identical on submission."""
        cleaned_data = super().clean()
        learning_language = cleaned_data.get('learning_language')
        known_language = cleaned_data.get('known_language')

        if learning_language and known_language and learning_language == known_language:
            raise forms.ValidationError(
                "The language you know cannot be the same as the language you are learning."
            )
            
        return cleaned_data
