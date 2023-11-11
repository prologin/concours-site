# Generated by Django 2.2.28 on 2023-11-11 19:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oidc_policy', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openidclientpolicy',
            name='allow_assigned_semifinal_event',
            field=models.ForeignKey(blank=True, help_text='Allow contestants of the current edition assigned to the selected semifinal event to login through this client.', limit_choices_to={'edition': 2024, 'type': 1}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contest.Event'),
        ),
    ]
