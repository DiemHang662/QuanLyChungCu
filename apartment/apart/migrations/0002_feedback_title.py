# Generated by Django 5.0.3 on 2024-05-05 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apart', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='title',
            field=models.CharField(default='Mất điện', max_length=70),
        ),
    ]
