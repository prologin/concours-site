# Generated by Django 2.2.28 on 2023-11-11 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0009_contestant_learn_about_contest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventwish',
            name='order',
            field=models.IntegerField(db_index=True),
        ),
    ]
