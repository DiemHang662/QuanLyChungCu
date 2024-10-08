# Generated by Django 5.0.3 on 2024-07-31 16:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apart', '0017_remove_billproduct_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_amount', models.DecimalField(decimal_places=0, max_digits=10)),
                ('order_date', models.DateField(auto_now_add=True)),
                ('status', models.CharField(choices=[('ĐANG CHỜ', 'Đang chờ'), ('ĐANG GIAO', 'Đang giao'), ('ĐANG VẬN CHUYỂN', 'Đang vận chuyển'), ('ĐÃ GIAO', 'Đã giao')], default='ĐANG CHỜ', max_length=30)),
                ('resident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_products', to='apart.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apart.product')),
            ],
        ),
        migrations.DeleteModel(
            name='BillProduct',
        ),
    ]
