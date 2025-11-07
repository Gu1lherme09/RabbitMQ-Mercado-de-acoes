from django import forms
from django.contrib.auth import authenticate
from .models import Usuario

class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar senha', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['email', 'telefone']

    def clean_email(self):
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'As senhas não conferem.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        password = cleaned.get('password')

        if not email or not password:
            raise forms.ValidationError('E-mail ou senha inválidos.')

        try:
            user_obj = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise forms.ValidationError('E-mail ou senha inválidos.')

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise forms.ValidationError('E-mail ou senha inválidos.')

        cleaned['user'] = user
        return cleaned
