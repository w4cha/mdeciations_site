# Generated by Django 5.1.1 on 2024-10-16 16:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('laboratorio', '0003_alter_directorgeneral_laboratorio_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='producto',
            options={'permissions': [('ver_margen', 'Puede ver el costo de producción y margen')]},
        ),
    ]
