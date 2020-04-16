from django.db import migrations, models

def update_qcm(apps, schema_editor):
    Question = apps.get_model('qcm', 'Question')
    alias = schema_editor.connection.alias
    Question.objects.using(alias).filter(body__icontains='%(BONUS)%').update(is_optional=True)

class Migration(migrations.Migration):

    dependencies = [
        ('qcm', '0002_question_is_optional'),
    ]

    operations = [
        migrations.RunPython(update_qcm)
    ]
