# Generated by Django 5.1.1 on 2024-10-16 18:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('laboratorio', '0004_alter_producto_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='laboratorio',
            options={'permissions': [('descargar', 'puede descargar las tablas')]},
        ),
    ]
