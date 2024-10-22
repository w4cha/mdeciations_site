from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.forms.models import model_to_dict
from django.db.models import F, Sum
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Laboratorio, DirectorGeneral, Producto, UserCart, ExtraUserInfo
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LabForm, DgForm, ProductForm, LoginForm, CreateUserForm, AddToCartForm, UpdateUserForm, UserAddressForm, UserUpdatePasswordForm
from django.contrib.auth import views as auth_views, authenticate, login
from django.contrib.auth.decorators import login_required
# so an user stays logged after password change
from django.contrib.auth import update_session_auth_hash
import csv
# Create your views here.

# used to table and form transitions between models using htmx
model_mapping = {1: Laboratorio,
                2: DirectorGeneral, 
                3: Producto}

# dynamically check permissions for views
permits_mapping = {1: "_laboratorio",
                  2: "_directorgeneral", 
                  3: "_producto"}

class IndexView(generic.TemplateView):

    template_name = 'laboratorio/index.html'


class UserCartView(LoginRequiredMixin, generic.ListView):

    template_name = 'laboratorio/cart.html'

    context_object_name = "compras"

    login_url = reverse_lazy("lab:inicio")

    redirect_field_name = "denied"

    def get_queryset(self):
        # you can access args passed from urls on class view via the kwargs attribute
        # this to prevent accessing to other users pages
        if self.request.user.username == self.kwargs.get("username"):
            return UserCart.objects.select_related("compra").filter(usuario__username=self.kwargs["username"]).annotate(subtotal=F("cantidad") * F("compra__venta_producto"))
        raise PermissionDenied
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total"] = UserCart.objects.filter(usuario__username=self.kwargs["username"]).aggregate(total=Sum(F("cantidad") * F("compra__venta_producto")))
        return context


class ProductView(generic.DetailView):

    template_name = 'laboratorio/detail.html'

    model = Producto

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context["form"] = AddToCartForm(self.kwargs["pk"])
        return context
    

class LabList(generic.ListView):

    template_name = 'laboratorio/list.html'

    context_object_name = "información_tabla"


    def get_queryset(self):
        # if you save something to a self 
        # you can latter access in the context dict
        if not (argument := self.request.GET.get("resultados", False)):
            self.download_all = "all"
            return Laboratorio.objects.values_list()
        else:
            self.download_all = argument
            return Laboratorio.objects.filter(nombre__icontains=argument).values_list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["thead"] = [field.verbose_name for field in 
                           Laboratorio._meta.get_fields() if field.name 
                           in ["nombre", "ciudad", "país",]]
        context["ntable"] = 1
        context["download"] = self.download_all
        return context
    
class LogOutView(auth_views.LogoutView):
    # donde se redirige después de salir de la cuenta
    next_page = "lab:inicio"

    # message on log out
    def get_success_url(self):
        messages.success(self.request, "sesión cerrada", "éxito")
        return super().get_success_url()

# additional arguments are the ones captured from the url pattern
# the argument in the url are (get, post, etc) are accesible
# bia request.POST.get or request.GET.get
def change_table(request):
    if request.META.get("HTTP_HX_REQUEST", False):
        # to support redirecting after delete request
        if request.method in ("POST", "GET", "DELETE"):
            # list and string are indexable so is fine 
            if request.method == "POST":
                tabla = request.POST.get("change", ["1",])[0]
            else:
                # by design other methods args are found in the get one
                tabla = request.GET.get("change", ["1",])[0]
            # since is a url query it has to be parse to int unlike if it was 
            # defined as an url pattern using <int>
            tabla = int(tabla) if tabla in [str(i) for i in range(1,4)] else 1
            current_table = model_mapping.get(tabla, Laboratorio)
            tables_mapping = {
                1: {"fields": [field.name for field in Laboratorio._meta.get_fields() if 
                                field.name not in ["laboratorio", "laboratorios"]],
                    "table_head": [field.verbose_name for field in 
                                   Laboratorio._meta.get_fields() if field.name 
                                   not in ["id", "laboratorio", "laboratorios"]]
                },
                2: {"fields": [field.name for field in DirectorGeneral._meta.get_fields() if 
                               field.name not in ["laboratorio"]] + ["laboratorio__nombre",],
                    "table_head": [field.verbose_name for field in 
                                   DirectorGeneral._meta.get_fields() if field.name 
                                   not in ["id"]] 
                },
                3: {"fields": [field.name for field in Producto._meta.get_fields() if 
                               field.name not in ["laboratorio", 
                                                  "producto", "disponibles", "descripción", 
                                                  "costo_producto", "url_imagen"]],
                    "table_head": [field.verbose_name for field in 
                                   Producto._meta.get_fields() if field.name 
                                   not in ["id", "laboratorio", "producto", 
                                           "disponibles", "descripción", "costo_producto", "url_imagen"]]}
            } 
            table_fields = tables_mapping[tabla]["fields"]
            thead = tables_mapping[tabla]["table_head"]
            if tabla == 3:
                if request.user.has_perm("laboratorio.ver_margen"):
                    table_fields += ["costo_producto",]
                    thead += [current_table._meta.get_field("costo_producto").verbose_name,]
                    table_fields += ["margen",]
                    thead += ["margen de ganancia",]
                if request.user.is_authenticated:
                    table_fields += ["disponibles"]
                    thead += ["cantidad disponible"]
                thead += [current_table._meta.get_field("laboratorio").verbose_name,]
                table_fields += ["laboratorio__nombre"] 
            tvalues = current_table.objects.order_by("nombre")
            download_all = "all"
            if request.method == "GET":
                if (argument := request.GET.get("resultados", False)):
                    download_all = argument
                    tvalues = current_table.objects.filter(nombre__icontains=argument).order_by("nombre")
            if tabla == 3 and request.user.has_perm("laboratorio.ver_margen"):
                tvalues = tvalues.annotate(margen=F("venta_producto")-F("costo_producto")).values_list(*table_fields)
            else:
                tvalues = tvalues.values_list(*table_fields)
            # dynamically check the permissions to the current model
            current_perms = {1: "_laboratorio", 2: "_directorgeneral", 3: "_producto"}
            context = {"thead": thead, "ntable": tabla, "tvalues": tvalues, "download": download_all, "perms": current_perms[tabla]}
            return render(request, "laboratorio/change_list.html", context)
    raise PermissionDenied

@login_required(login_url=reverse_lazy("lab:inicio"))
def create_entry(request, tabla):
    form_mapping = {1: LabForm,
                     2: DgForm, 
                     3: ProductForm}
    
    if request.META.get("HTTP_HX_REQUEST", False) and request.user.has_perm(f"laboratorio.add{permits_mapping[tabla]}"):
        if request.method == "POST":
            current_form = form_mapping.get(tabla, LabForm)
            if tabla == 3:
                # this only works if the field to exclude has a default value
                if request.user.has_perm("laboratorio.reponer_producto"):
                    form = current_form(True, request.POST)
                else:
                    form = current_form(False, request.POST)
            else:
                form = current_form(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "entrada creada exitosamente", "éxito")
                if tabla != 3:
                    context = {"form": current_form(), "ntable": tabla, "crud": "create"}
                else:
                    if request.user.has_perm("laboratorio.reponer_producto"):
                        context = {"form": current_form(True), "ntable": tabla, "crud": "create"}
                    else:
                        context = {"form": current_form(False), "ntable": tabla, "crud": "create"}
                # render is a type of HttpResponse
                response = render(request, "laboratorio/add.html", context, status=200)
                response.headers['HX-Trigger'] = "reload"
                return response
            else:
                context = {"form": form, "ntable": tabla, "crud": "create"}
                return render(request, "laboratorio/add.html", context, status=200)
        elif request.method == "GET":
            current_form = form_mapping.get(tabla, LabForm)
            if tabla != 3:
                context = {"form": current_form(), "ntable": tabla, "crud": "create"}
            else:
                if request.user.has_perm("laboratorio.reponer_producto"):
                    context = {"form": current_form(True), "ntable": tabla, "crud": "create"}
                else:
                    context = {"form": current_form(False), "ntable": tabla, "crud": "create"}
            return render(request, "laboratorio/add.html", context, status=200)
    raise PermissionDenied

@login_required(login_url=reverse_lazy("lab:inicio"))
def delete_entry(request, tabla, pk):
    if request.META.get("HTTP_HX_REQUEST", False) and request.user.has_perm(f"laboratorio.delete{permits_mapping[tabla]}"):
        if request.method == "DELETE":
            # remember that the args are passed as str when using re_path
            current_table = model_mapping.get(tabla, Laboratorio)
            # if pk is a str django can treat it as an int
            delete_entry = get_object_or_404(current_table, pk=pk)
            table_fields = [field.name for field in current_table._meta.get_fields() if 
                                field.name not in ["laboratorio", "laboratorios", 
                                                   "descripción", "url_imagen", "disponibles", "id"]]
            if tabla != 1:
                table_fields += ["laboratorio__nombre"]
            old_entry = model_to_dict(instance=delete_entry, fields=table_fields)
            old_entry = ", ".join([f"{key}: {value}" for key, value in old_entry.items()])
            delete_entry.delete()
            messages.success(request, f"Entrada borrada exitosamente<br> {old_entry}", "éxito")
            # redirect by default is the current request method with the current headers
            url_302 = reverse("lab:other-list") + f"?change={tabla}"
            new_response = HttpResponseRedirect(redirect_to=url_302)
            return new_response
        elif request.method == "GET":
            current_entry_name = get_object_or_404(model_mapping.get(tabla, Laboratorio), pk=pk)
            context = {"entry": pk, "ntable": tabla, "elabel": current_entry_name.nombre}
            return render(request, "laboratorio/delete.html", context)
    raise PermissionDenied


@login_required(login_url=reverse_lazy("lab:inicio"))
def update_entry(request, tabla, pk):
    form_model_mapping = {1: [LabForm, Laboratorio],
                     2: [DgForm, DirectorGeneral], 
                     3: [ProductForm, Producto]}
                       
    if request.META.get("HTTP_HX_REQUEST", False) and request.user.has_perm(f"laboratorio.change{permits_mapping[tabla]}"):
        if request.method == "POST":
            current_form = form_model_mapping.get(tabla, [LabForm, Laboratorio])
            object_instance = get_object_or_404(current_form[1], pk=pk)
            if tabla == 3:
                if request.user.has_perm("laboratorio.reponer_producto"):
                    form = current_form[0](True, request.POST, instance=object_instance)
                else:
                    form = current_form[0](False, request.POST, instance=object_instance)
            else:
                form = current_form[0](request.POST, instance=object_instance)
            if form.is_valid():
                form.save()
                messages.success(request, "entrada modificada correctamente", "éxito")
                if tabla != 3:
                    context = {"form": current_form[0](instance=object_instance), "ntable": tabla, "crud": "update", "pk": pk}
                else:
                    if request.user.has_perm("laboratorio.reponer_producto"):
                        context = {"form": current_form[0](True, instance=object_instance), "ntable": tabla, "crud": "update", "pk": pk}

                    else:
                        context = {"form": current_form[0](False, instance=object_instance), "ntable": tabla, "crud": "update", "pk": pk}
                # render is a type of HttpResponse
                response = render(request, "laboratorio/add.html", context, status=200)
                response.headers['HX-Trigger'] = "reload"
                return response
            else:
                context = {"form": form, "ntable": tabla, "crud": "update", "pk": pk}
                return render(request, "laboratorio/add.html", context, status=200)
        elif request.method == "GET":
            current_form = form_model_mapping.get(tabla, [LabForm, Laboratorio])
            object_instance = get_object_or_404(current_form[1], pk=pk)
            if tabla == 3:
                if request.user.has_perm("laboratorio.reponer_producto"):
                    form_instance = current_form[0](True, instance=object_instance)
                else:
                    form_instance = current_form[0](False, instance=object_instance)
            else:
                form_instance = current_form[0](instance=object_instance)
            context = {"form": form_instance, "ntable": tabla, "crud": "update", "pk": pk}
            return render(request, "laboratorio/add.html", context, status=200)
    raise PermissionDenied

@login_required(login_url=reverse_lazy("lab:inicio"))
def get_csv(request, tabla):
    if request.method == "GET" and request.user.has_perm(f"laboratorio.view{permits_mapping[tabla]}"):
        current_table = model_mapping.get(tabla, Laboratorio)
        table_fields = [field.name for field in current_table._meta.get_fields() if 
                        field.name not in ["id", "laboratorio", "laboratorios", "producto", "url_imagen"]]
        thead = [field.verbose_name for field in 
                 current_table._meta.get_fields() if field.name 
                 not in ["id", "laboratorio", "laboratorios", "producto"]]
        if tabla != 1:
            thead = [field.verbose_name for field in 
                     current_table._meta.get_fields() if field.name 
                     not in ["id", "producto", "url_imagen"]]
            if tabla == 2:
                table_fields += ["laboratorio__nombre"]
            else:
                table_fields += ["margen", "laboratorio__nombre"]
                thead.append("margen")
                thead.append(thead.pop(1))
                    
        tvalues = current_table.objects.order_by("nombre")
        if (argument := request.GET.get("resultados", "all")):
                if argument != "all":
                    tvalues = current_table.objects.filter(nombre__icontains=argument).order_by("nombre")
        if tabla == 3:
            tvalues = tvalues.annotate(margen=F("venta_producto")-F("costo_producto")).values_list(*table_fields)
        else:
            tvalues = tvalues.values_list(*table_fields)
        if tvalues:
            response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{current_table.__name__.lower()}.csv"'},
            )
            # HttpResponse is already a pseudo file so i can write directly to it
            writer = csv.writer(response, delimiter="|")
            writer.writerow(thead)
            for item in tvalues:
                writer.writerow(list(item))
            return response
        else:
           messages.error(request, "no hay datos disponibles", "error")
           return HttpResponseRedirect(redirect_to=reverse("laboratorio:lista"), status = 302)
    else:
        raise PermissionDenied
    

def log_user_in(request):
    if request.META.get("HTTP_HX_REQUEST", False) and not request.user.is_authenticated:
        if request.method == "POST":
            # the data part is required
            form = LoginForm(data=request.POST)
            # by default a form suing AuthenticationForm saves in user_cache 
            # the authenticated user if the form was valid so you can directly
            # use login without using authenticate
            if form.is_valid():
                # check that the user was authenticated and that the session is still active
                if form.user_cache is not None and form.user_cache.is_active:
                    login(request, form.user_cache)
                    messages.success(request, f"Bienvenido {form.cleaned_data.get('username')}", "éxito")
                new_response = HttpResponse()
                new_response["HX-Redirect"] = reverse("lab:inicio")
                return new_response
            context = {"form": form, "action": "login", "origen": "main"}
            if (site_part := request.POST.get("origen", False)):
                context["origen"] = site_part
            return render(request, "registration/login.html", context, status=200)
        elif request.method == "GET":
            form = LoginForm()
            context = {"form": form, "action": "login", "origen": "main"}
            if request.GET.get("origen", False):
                context["origen"] = "producto"
            return render(request, "registration/login.html", context)
    raise PermissionDenied


def new_user(request):
    if request.META.get("HTTP_HX_REQUEST", False) and not request.user.is_authenticated:
        if request.method == "POST":
            # the data part is required
            form = CreateUserForm(data=request.POST)
            if form.is_valid():
                form.save()
                # check that the user was authenticated and that the session is still active
                username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
                # new_user has is_active
                new_user = authenticate(username=username, password=password)
                if new_user is not None:
                    login(request, new_user)
                    messages.success(request, f"Bienvenido {form.cleaned_data.get('username')}", "éxito")
                new_response = HttpResponse()
                new_response["HX-Redirect"] = reverse("lab:inicio")
                return new_response
            context = {"form": form, "action": "sign", "origen": "main"}
            if (site_part := request.POST.get("origen", False)):
                context["origen"] = site_part
            return render(request, "registration/login.html", context, status=200)
        elif request.method == "GET":
            form = CreateUserForm()
            context = {"form": form, "action": "sign", "origen": "main"}
            if request.GET.get("origen", False):
                context["origen"] = "producto"
            return render(request, "registration/login.html", context)
    raise PermissionDenied


@login_required(login_url=reverse_lazy("lab:inicio"))
# for displaying and updating user personal info
def user_profile(request, username):
    if request.user.username == username:
        current_user = get_object_or_404(User, username=username)
        if request.method == "POST":
            current_address = get_object_or_404(ExtraUserInfo, usuario__pk=request.user.pk)
            if request.POST.get("username", False):
                form_password = UserUpdatePasswordForm(request.user)
                update_user = UpdateUserForm({key: value for key, 
                                            value in request.POST.items() 
                                            if key in ["username", "email", 
                                                        "first_name", "last_name"]}, instance=current_user)
                update_extra_info = UserAddressForm({key: value for key, 
                                                    value in request.POST.items() 
                                                    if key == "dirección"}, instance=current_address)
                all_valid = [update_user, update_extra_info]
                if all([update_model.is_valid() for update_model in all_valid]):
                    for item in all_valid:
                        item.save()
                    messages.success(request, "información actualizada con éxito", "éxito")
                context = {"form_user": update_user, "form_address": update_extra_info, "form_password": form_password}
            elif request.POST.get("old_password", False):
                update_form_password = UserUpdatePasswordForm(request.user, request.POST)
                if update_form_password.is_valid():
                    update_form_password.save()
                    update_session_auth_hash(request, update_form_password.user)
                    messages.success(request, "contraseña actualizada", "éxito")
                form_user = UpdateUserForm(instance=current_user)
                form_address = UserAddressForm(instance=current_address)
                context = {"form_user": form_user, "form_address": form_address, "form_password": update_form_password}
            return render(request, "laboratorio/profile.html", context, status=200)
            
        elif request.method == "GET":
            # returns a tuple
            current_user_address, _ = ExtraUserInfo.objects.get_or_create(usuario__pk=request.user.pk, defaults={"usuario": current_user})
            form_user = UpdateUserForm(instance=current_user)
            form_address = UserAddressForm(instance=current_user_address)
            form_password = UserUpdatePasswordForm(request.user)
            context = {"form_user": form_user, "form_address": form_address, "form_password": form_password}
            return render(request, "laboratorio/profile.html", context)
    raise PermissionDenied


@login_required(login_url=reverse_lazy("lab:inicio"))
def delete_profile(request, username):
    if request.META.get("HTTP_HX_REQUEST", False) and request.user.username == username:
        if request.method == "DELETE":
            # remember that the args are passed as str when using re_path
            current_user = get_object_or_404(User, username=username)
            current_user.delete()
            messages.success(request, f"su cuenta ha sido terminada exitosamente", "éxito")
            # redirect by default is the current request method with the current headers
            new_response = HttpResponse()
            new_response["HX-Redirect"] = reverse("lab:inicio")
            return new_response
        elif request.method == "GET":
            context = {"entry": 0, "ntable": 0, "elabel": request.user.username}
            return render(request, "laboratorio/delete.html", context)
    raise PermissionDenied


@login_required(login_url=reverse_lazy("lab:inicio"))
def add_to_cart(request, pk):
    if request.META.get("HTTP_HX_REQUEST", False) and request.method == "POST":
        form = AddToCartForm(pk, request.POST)
        if form.is_valid():
            # is safe to use cleaned_data instead of clean_cantidad
            # since the validation was made already on is_valid()
            UserCart.objects.create(compra=Producto.objects.get(pk=pk), 
                                    cantidad=form.cleaned_data["cantidad"],
                                    usuario=User.objects.get(pk=request.user.id))
            Producto.objects.filter(pk=pk).update(disponibles=F("disponibles") - form.cleaned_data["cantidad"])
            link_args = {'username': request.user.username}
            link = (f'<a href = {reverse("lab:cart", kwargs=link_args)} class="link-primary link-offset-2 link-underline-opacity-25 '
                    'link-underline-opacity-100-hover">ver detalle</a>')
            messages.success(request, f"{form.cleaned_data['cantidad']} añadido al carro {link}", "éxito")
            # like this to update the quantity after each purchase
            if request.POST.get("rigen_buy") == "products":
                context = {"object": Producto.objects.get(pk=pk), "form": AddToCartForm(pk), "cart": False}
                response = render(request, "laboratorio/detail.html", context)
                response.headers['HX-Trigger'] = "reload"
            else:
                context = {"object": Producto.objects.get(pk=pk), "form": AddToCartForm(pk), "cart": True}
                response = render(request, "laboratorio/detail.html", context)
            return response

        # like this to keep the errors from the previous instance
        context = {"object": Producto.objects.get(pk=pk), "form": AddToCartForm(pk)}
        context["form"] = form   
        return render(request, "laboratorio/detail.html", context)
    raise PermissionDenied


@login_required(login_url=reverse_lazy("lab:inicio"))
def delete_cart_item(request, pk):
    if request.META.get("HTTP_HX_REQUEST", False):
        if request.method == "DELETE":
            to_delete = get_object_or_404(UserCart, pk=pk)
            current_quantity = to_delete.cantidad
            current_product = to_delete.compra.pk
            message_context = (f"Compra por ${to_delete.cantidad * to_delete.compra.venta_producto:.2f} "
                               f"del producto {to_delete.compra.nombre} (cantidad: {to_delete.cantidad}) eliminada del carro")
            to_delete.delete()
            Producto.objects.filter(pk=current_product).update(disponibles=F("disponibles") + current_quantity)
            messages.success(request, message_context, "éxito")
            # redirect by default is the current request method with the current headers
            new_response = HttpResponse()
            new_response["HX-Redirect"] = reverse("lab:cart", kwargs={"username": request.user.username})
            return new_response
        elif request.method == "GET":
            current_entry_name = get_object_or_404(UserCart, pk=pk)
            context = {"entry": pk, "ntable": 0, "elabel": current_entry_name.__str__()}
            return render(request, "laboratorio/delete.html", context)
    raise PermissionDenied
