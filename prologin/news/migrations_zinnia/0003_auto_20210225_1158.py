# Generated by Django 2.2.19 on 2021-02-25 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zinnia', '0002_zinnia_0003_publication_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='level',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='category',
            name='lft',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='category',
            name='rght',
            field=models.PositiveIntegerField(editable=False),
        ),
    ]
