from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import MyUser, ProductModel, PurchaseModel, ReturnModel


class RegisterForm(UserCreationForm):
    class Meta:
        model = MyUser
        fields = ["username", ]


class AppendForm(ModelForm):
    class Meta:
        model = ProductModel
        exclude = []


class BuyForm(ModelForm):
    class Meta:
        model = PurchaseModel
        fields = ["count"]


class ReturnForm(ModelForm):
    class Meta:
        model = ReturnModel
        fields = []
