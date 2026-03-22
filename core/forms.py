from django import forms
from .models import ServiceRequest

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['customer_name', 'email', 'mobile_number', 'laptop_model', 'problem_type', 'problem_description', 'photos']

class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Enter your full name',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
    }))
    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Choose a username',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'your@email.com',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Min 8 characters',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm password',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
    }))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        if password and len(password) < 8:
            self.add_error('password', "Password must be at least 8 characters.")
            
        return cleaned_data

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={
        'placeholder': '0 0 0 0 0 0',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-center tracking-[0.5em] text-2xl font-bold font-mono',
        'type': 'number',
        'oninput': 'if(this.value.length > 6) this.value = this.value.slice(0,6);'
    }))
