# Generated by Django 5.0.3 on 2024-07-18 15:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apart', '0010_remove_product_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='items',
        ),
    ]