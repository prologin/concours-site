# Generated by Django 2.0.4 on 2018-04-04 14:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_states', to='forum.Post')),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_states', to='forum.Thread')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_states', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='readstate',
            unique_together={('thread', 'user')},
        ),
    ]
