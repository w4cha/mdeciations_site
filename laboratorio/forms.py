from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Laboratorio, DirectorGeneral, Producto, ExtraUserInfo
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from datetime import date


class LabForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["país"].widget = forms.widgets.TextInput(attrs={"list":"countries"})
        
    class Meta:
        model = Laboratorio
        fields = "__all__"


class DgForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["laboratorio"].widget = forms.widgets.Select(choices=tuple(((query.id, query.nombre) for query in Laboratorio.objects.all())))
    
    class Meta:
        model = DirectorGeneral
        fields = "__all__"


class ProductForm(forms.ModelForm):

    # like this to pass custom args and do actions depending on them
    # in this case mute some fields if the user does not have
    # the proper permissions
    def __init__(self, permiso, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not permiso:
            if "disponibles" in self.fields:
                del self.fields["disponibles"]

        # use textinput instead of date that solves the display of current data when updating an entry
        self.fields["fecha_fabricación"].widget = forms.widgets.TextInput(attrs={'value':f'{date.today()}', 'type':'date'})
        # firs in tuple the value the second the text
        self.fields["laboratorio"].widget = forms.widgets.Select(choices=tuple(((query.id, query.nombre) for query in Laboratorio.objects.all())))
        self.fields["descripción"].widget = forms.widgets.Textarea(attrs={'rows': 5, 'cols': 30})

    
    class Meta:
        model = Producto
        fields = "__all__"


class LoginForm(AuthenticationForm):

    error_messages = {
        "invalid_login": "Nombre de usuario <br> o contraseña inválidos",
        "inactive": "Acceso denegado",
    }

class CreateUserForm(UserCreationForm): 
  
  email = forms.EmailField(required=True)

  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = """
        Longitud máxima de 150 caracteres alfanuméricos <br>
        (letras, dígitos y @/./+/-/_ como caracteres aceptados).
        """
        self.fields["password1"].help_text = """
    Consideraciones:<br>
    1. Su contraseña no puede ser muy similar a su otra información personal<br>
    2. Su contraseña debe contener al menos 8 caracteres<br>
    3. Su contraseña no puede ser una contraseña de uso común<br>
    4. Su contraseña no puede ser completamente numérica

"""

  class Meta:
      model = User
      fields = ['username', 'email', 'password1', 'password2',]


class AddToCartForm(forms.Form):

    def __init__(self, entry_pk, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_value = Producto.objects.get(pk=entry_pk)
        self.fields["cantidad"].widget.attrs.update({"min": 1, "max": self.max_value.disponibles, 
                                                     "value": 1, "onchange": f"update_total({self.max_value.venta_producto});"})

    cantidad = forms.IntegerField(validators=[MinValueValidator(1, message="debe elegir al menos 1 producto")])

    # this way to apply the clean to only the specific field
    def clean_cantidad(self):
        value = self.cleaned_data["cantidad"]
        if value > self.max_value.disponibles:
            raise ValidationError("no existen los suficientes items para su compra")
        return value


# UserChangeForm is not that useful better to use 
# form.Model with User model to update data
class UpdateUserForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "máximo 150 caracteres <br> solo letras dígitos o @/./+/-/_"
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

# this is required since django does not let you update a password using UserChangeForm directly
class UserUpdatePasswordForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ("mínimo 8 caracteres <br> de preferencia que no sea similar<br>"
                                              "a otra información personal <br> ni una contraseña común")
        self.fields["new_password2"].label = "Confirmación de contraseña"
        self.fields["new_password2"].help_text = "reingrese su contraseña nueva"

class UserAddressForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dirección"].widget = forms.widgets.Textarea(attrs={'rows': 4, 'cols': 25})
        self.fields["dirección"].help_text = "dirección de envío para <br> los productos que compres"

    class Meta:
        model = ExtraUserInfo
        exclude = ['usuario',]