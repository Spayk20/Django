from django.contrib import admin
from .models import *

admin.site.register(MyUser)
admin.site.register(ProductModel)
admin.site.register(PurchaseModel)
admin.site.register(ReturnModel)
