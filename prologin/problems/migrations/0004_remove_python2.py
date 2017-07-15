from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_replace_exec_stats_with_result'),
    ]

    operations = [
        migrations.RunSQL('''
            UPDATE problems_submissioncode
            SET language = 'python'
            WHERE language = 'python2' OR language = 'python3'
        '''),

        migrations.RunSQL('''
            UPDATE contest_contestant
            SET preferred_language = 'python'
            WHERE preferred_language = 'python2' OR preferred_language = 'python3'
        ''')
    ]
