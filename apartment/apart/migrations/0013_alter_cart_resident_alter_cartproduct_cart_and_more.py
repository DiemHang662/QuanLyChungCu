# Generated by Django 5.0.3 on 2024-07-18 15:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apart', '0012_alter_cartproduct_cart_alter_cartproduct_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='resident',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cartproduct',
            name='cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apart.cart'),
        ),
        migrations.AlterField(
            model_name='cartproduct',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apart.product'),
        ),
    ]
