from django import forms


class EmailSubscribeForm(forms.Form):
    email = forms.EmailField(label='Adresse électronique', max_length=100)
