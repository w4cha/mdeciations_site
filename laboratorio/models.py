from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Upper
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from datetime import date

# Create your models here.

class Laboratorio(models.Model):

    nombre = models.CharField(verbose_name="Nombre del laboratorio", max_length=50)

    ciudad = models.CharField(verbose_name="Ciudad de origen", max_length=35)

    país = models.CharField(verbose_name="País de origen", max_length=35)

    class Meta:

        constraints = [
        models.UniqueConstraint(Upper("nombre"), 
                                name='unique laboratorio upper',
                                violation_error_message='El nombre del laboratorio ya existe'),
        ]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        self.ciudad = self.ciudad.upper()
        self.país = self.país.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Laboratorio: {self.nombre}"


class DirectorGeneral(models.Model):

    nombre = models.CharField(verbose_name="Nombre del director", max_length=30)

    especialidad = models.CharField(verbose_name="Especialidad del director", max_length=30)

    laboratorio = models.OneToOneField(Laboratorio, on_delete=models.CASCADE, 
                                       related_name="laboratorio", verbose_name="Laboratorio que dirige")

    class Meta:

        verbose_name_plural = "Directores generales"

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        self.especialidad = self.especialidad.upper()
        super().save(*args, **kwargs)
       
    def __str__(self):
        return f"Director: {self.nombre}, Laboratorio: {self.laboratorio.nombre}"
    

class Producto(models.Model):

    nombre = models.CharField(verbose_name="Nombre del producto", max_length=50)

    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE, 
                                    related_name="laboratorios", verbose_name="Laboratorio de origen")

    fecha_fabricación = models.DateField(verbose_name="Fecha de fabricación", 
                                         validators=[MaxValueValidator(date.today, message="fecha debe ser antes que %(limit_value)s"), 
                                                     MinValueValidator(date(2015, 1, 1), message="fecha debe ser después de %(limit_value)s")])

    # max_digits include decimal places
    costo_producto = models.DecimalField(verbose_name="Costo fabricación", decimal_places=2, max_digits=12,
                                         validators=[MinValueValidator(0.00, message="el valor debe ser un número positivo"),])

    venta_producto = models.DecimalField(verbose_name="Precio de venta", decimal_places=2, max_digits=12, 
                                         validators=[MinValueValidator(0.00, message="el valor debe ser un número positivo"),])
    
    disponibles = models.PositiveIntegerField(verbose_name="cantidad disponible", default=0, validators=[MaxValueValidator(100, message="no se puede tener más de %(limit_value)s de este item en stock")])

    descripción = models.CharField(verbose_name="descripción producto", max_length=200)

    url_imagen = models.URLField(verbose_name="imagen producto", max_length=120, default="https://i.imgur.com/F7rzwZ5.jpeg")

    class Meta:

        constraints = [
        models.UniqueConstraint(Upper("nombre"), 
                                name='unique Producto upper',
                                violation_error_message='El nombre del producto ya existe'),
        ]

        permissions = [
            (
                "ver_margen",
                "Puede ver el costo de producción y margen",
            ),
            (
                "reponer_producto",
                "Puede aumentar la cantidad de stock disponible del producto",
            )
        ]

    # method implemented to wite your own validations at model level
    def clean(self, *args, **kwargs):
        if self.costo_producto > self.venta_producto:
            raise ValidationError(f"el precio de venta ({self.venta_producto}) "
                                  f"no puede ser menor que el de producción ({self.costo_producto})")
        super().clean(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return (f"Producto: {self.nombre}, Laboratorio: {self.laboratorio.nombre}, Fecha fabricación: {self.fecha_fabricación}, "
                f"Costo producción: {self.costo_producto}, Precio venta: {self.venta_producto}")
    

class UserCart(models.Model):
    compra = models.ForeignKey(Producto, on_delete=models.CASCADE,
                               related_name="producto", verbose_name="Compra")
    cantidad = models.PositiveIntegerField(verbose_name="cantidad a comprar", default=0)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comprador", verbose_name="Usuario de la compra")


    def __str__(self):
        return f'compra: {self.compra.nombre or "nada"}, cantidad: {self.cantidad}, total: ${self.compra.venta_producto * self.cantidad}'
    
    
class ExtraUserInfo(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="dirección", verbose_name="dirección del usuario")
    dirección = models.CharField(verbose_name="dirección de envío", max_length=100, blank=True, null=True)
    

