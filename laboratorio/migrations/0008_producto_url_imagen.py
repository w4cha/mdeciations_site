# Generated by Django 5.1.1 on 2024-10-18 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratorio', '0007_alter_producto_options_producto_descripción_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='url_imagen',
            field=models.URLField(default='https://i.imgur.com/F7rzwZ5.jpeg', max_length=120, verbose_name='imagen producto'),
        ),
    ]
