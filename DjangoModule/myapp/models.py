from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.utils import timezone

from myapp.my_exseptions import NotMuchCount, NotMuchMoney, NotZeroCount, TimeUp
from mysite import settings


class MyUser(AbstractUser):
    money = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.username


class ProductModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование', blank=False, null=False)
    about = models.TextField(max_length=1000, verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    count = models.PositiveIntegerField(verbose_name='Наличие на складе')

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseModel(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.DO_NOTHING, related_name="purchases")
    product = models.ForeignKey(ProductModel, on_delete=models.DO_NOTHING, related_name="purchases")
    count = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)
    return_status = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        need_count = self.count
        product = self.product
        user = self.user
        if product.count >= need_count != 0 and user.money >= (product.price * need_count):
            product.count -= need_count
            user.money -= (product.price * need_count)
            with transaction.atomic():
                user.save()
                product.save()
                super(PurchaseModel, self).save(*args, **kwargs)
        elif product.count < need_count:
            raise NotMuchCount()
        elif user.money < (product.price * need_count):
            raise NotMuchMoney()
        elif need_count == 0:
            raise NotZeroCount

    def __str__(self):
        return f"{self.product}"


class ReturnModel(models.Model):
    purchase = models.ForeignKey(PurchaseModel, on_delete=models.CASCADE, related_name="returns")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        purchase = self.purchase
        if (timezone.now() - purchase.date).seconds < settings.PURCHASE_RETURN_TIME*60:
            purchase.status = True
            with transaction.atomic():
                purchase.save()
                super(ReturnModel, self).save(*args, **kwargs)
        else:
            raise TimeUp()

    def __str__(self):
        return f"{self.purchase}"
