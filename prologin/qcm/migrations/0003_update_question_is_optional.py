from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qcm', '0002_question_is_optional'),
    ]

    operations = [
        migrations.RunSQL('''
            UPDATE qcm_question
            SET is_optional = true
            WHERE body LIKE '%(BONUS)%'
        ''')
    ]
