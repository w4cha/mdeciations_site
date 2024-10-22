from django.contrib import admin
from .models import Laboratorio, DirectorGeneral, Producto

# Register your models here.

# this is connected to the model defined
# in this class model relation field
class DirectorInline(admin.TabularInline):

    model = DirectorGeneral

    extra = 0

class ProductoInline(admin.TabularInline):

    model = Producto

    extra = 0

class LaboratorioAdmin(admin.ModelAdmin):

    list_display = ["nombre",]

    ordering = ["nombre",]

    inlines = [DirectorInline, ProductoInline,]


class DirectorAdmin(admin.ModelAdmin):

    list_display = ["nombre", "laboratorio__nombre",]

    ordering = ["nombre",]

    list_filter = ["laboratorio__nombre",]


class ProductoAdmin(admin.ModelAdmin):

    list_display = ["nombre", "laboratorio__nombre", "costo_producto", "venta_producto", "margen_producto",
                    *[field.name for field in 
                      Producto._meta.get_fields() if field.name in ["disponibles", "descripción", "url_imagen",]],]
    
    ordering = ["nombre", "laboratorio__nombre",]

    list_filter = ["nombre", "laboratorio__nombre",]

    def margen_producto(self, obj):
        return obj.venta_producto - obj.costo_producto


admin.site.register(Laboratorio, LaboratorioAdmin)
admin.site.register(DirectorGeneral, DirectorAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.site_title = 'Administración'
