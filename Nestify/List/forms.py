from django import forms
from .models import ListItem, List  # Ensure you import the correct model

class ListItemForm(forms.ModelForm):
    class Meta:
        model = ListItem
        fields = ["name", "qty"]

    name = forms.CharField(
        label="Pavadinimas",
        widget=forms.TextInput(attrs={"placeholder": "Įveskite pavadinimą", "class": "form-control"})
    )

    qty = forms.IntegerField(
        label="Kiekis",
        widget=forms.NumberInput(attrs={"placeholder": "įveskite kiekį", "class": "form-control", "min": 1})
    )

class ListForm(forms.ModelForm):
    class Meta:
        model = List
        fields = ["name"]

    name = forms.CharField(
        label="Pavadinimas",
        widget=forms.TextInput(attrs={"placeholder": "Įveskite pavadinimą", "class": "form-control"})
    )
