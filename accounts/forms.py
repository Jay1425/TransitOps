from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "input-field text-sm py-3 w-full border border-slate-300 rounded-lg px-3 focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Enter your username",
            "autofocus": True,
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "input-field text-sm py-3 w-full border border-slate-300 rounded-lg px-3 focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Enter your password",
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            "class": "rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
        })
    )