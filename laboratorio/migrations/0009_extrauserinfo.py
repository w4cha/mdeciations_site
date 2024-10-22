# Generated by Django 5.1.1 on 2024-10-20 16:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratorio', '0008_producto_url_imagen'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtraUserInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dirección', models.CharField(max_length=60, verbose_name='dirección de envío')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='dirección', to=settings.AUTH_USER_MODEL, verbose_name='dirección del usuario')),
            ],
        ),
    ]