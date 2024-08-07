# Generated by Django 5.0.3 on 2024-07-22 15:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apart', '0014_alter_cart_resident_alter_cartproduct_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bill_products', to='apart.bill')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apart.product')),
            ],
        ),
    ]
