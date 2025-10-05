from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
        return user



class ProfileUpdateForm(forms.ModelForm):
    """Allow users to update basic account fields.

    Security considerations:
    - Username uniqueness is validated excluding the current user.
    - Email is optional to match RegistrationForm.
    """

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("Username cannot be empty.")
        # Ensure username is unique except for the current instance
        qs = User.objects.filter(username=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class AccountDeletionForm(forms.Form):
    """Require explicit confirmation phrase and password before deletion."""

    confirm_text = forms.CharField(
        max_length=10,
        help_text="Type DELETE to confirm",
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_confirm_text(self):
        value = (self.cleaned_data.get("confirm_text") or "").strip()
        if value != "DELETE":
            raise forms.ValidationError("You must type DELETE in all caps to confirm.")
        return value
