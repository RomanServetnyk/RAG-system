# Generated by Django 3.2.6 on 2023-12-03 21:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbaseapp', '0005_chat'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
