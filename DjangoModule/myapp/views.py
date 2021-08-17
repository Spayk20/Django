from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from .models import *
from .forms import RegisterForm, AppendForm, BuyForm, ReturnForm


class Login(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return '/profile/{}/'.format(self.request.user.id)


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = '/login/'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.money = 10000
        obj.save()
        return super().form_valid(form=form)


class Logout(LoginRequiredMixin, LogoutView):
    next_page = '/'
    login_url = '/login/'


class PurchasesList(ListView):
    model = PurchaseModel
    template_name = "purchases.html"
    extra_context = {'form': ReturnForm}
    paginate_by = 3


class Profile(LoginRequiredMixin, DetailView):
    login_url = "/login/"
    pk_url_kwarg = "pk"
    model = MyUser
    template_name = "profile.html"


class ProductListView(ListView):
    model = ProductModel
    template_name = 'index.html'
    paginate_by = 3


class ProductAppend(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    form_class = AppendForm
    template_name = "add_product.html"
    success_url = '/'


class ProductUpdate(LoginRequiredMixin, UpdateView):
    login_url = "/login/"
    template_name = "change_product.html"
    model = ProductModel
    fields = ["name", "about", "price", "count"]

    def get_success_url(self):
        return "/product/about/{}".format(self.object.pk)


class ProductAbout(DetailView):
    model = ProductModel
    template_name = "product.html"
    extra_context = {"form": BuyForm}


class ProductBuy(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    form_class = BuyForm
    paginate_by = 3

    def form_valid(self, form):
        try:
            purchase = form.save(commit=False)
            purchase.user = self.request.user
            purchase.product = ProductModel.objects.get(pk=self.kwargs["pk"])
            purchase.save()
            return HttpResponseRedirect(self.get_success_url())
        except NotMuchMoney:
            return messages.error(self.request, "У вас недостаточно денег")
        except NotMuchCount:
            return messages.error(self.request, "У нас недостаточно продуктов")
        except NotZeroCount:
            return messages.error(self.request, "Заказ должень иметь хотя-бы одну позицию")
        finally:
            return redirect(f"/product/about/{self.kwargs['pk']}")

    def get_success_url(self):
        return "/user/purchases/"


class Return(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    form_class = ReturnForm

    def form_valid(self, form):
        purchase = PurchaseModel.objects.get(pk=self.kwargs["pk"])
        try:
            purchase_return = form.save(commit=False)
            purchase_return.purchase = purchase
            purchase_return.save()
        except TimeUp:
            purchase.return_status = True
            purchase.status = True
            purchase.save()
            messages.info(self.request, "Время вышло")
        finally:
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return "/user/purchases/"


class Reject(DeleteView):
    model = ReturnModel
    success_url = "/products/returns/"

    def delete(self, request, success_url=success_url, *args, **kwargs):
        return_object = self.get_object()
        purchase = return_object.purchase
        purchase.return_status = True
        with transaction.atomic():
            purchase.save()
            return_object.delete()
        return HttpResponseRedirect(success_url)


class Accept(DeleteView):
    model = PurchaseModel
    success_url = "/products/returns/"

    def delete(self, request, success_url=success_url, *args, **kwargs):
        purchase_object = self.get_object()
        product = purchase_object.product
        user = purchase_object.user
        user.money += product.price * purchase_object.count
        product.count += purchase_object.count
        with transaction.atomic():
            user.save()
            product.save()
            purchase_object.delete()
        return HttpResponseRedirect(success_url)


class ReturnHandler(ListView):
    model = ReturnModel
    template_name = "returns.html"
    paginate_by = 3