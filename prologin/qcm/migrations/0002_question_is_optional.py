from django.db import migrations, models

def update_qcm(apps, schema_editor):
    Question = apps.get_model('qcm', 'Question')
    alias = schema_editor.connection.alias
    Question.objects.using(alias).filter(body__icontains='%(BONUS)%').update(is_optional=True)


class Migration(migrations.Migration):

    dependencies = [
        ('qcm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_optional',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(update_qcm),
    ]
