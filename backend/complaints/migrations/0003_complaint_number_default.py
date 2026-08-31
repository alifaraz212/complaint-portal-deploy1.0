from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_alter_category_options_alter_activitylog_complaint_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE complaints_complaint
                ALTER COLUMN complaint_number
                SET DEFAULT 'CMP-' || lpad(nextval('complaint_number_seq')::text, 5, '0');
            """,
            reverse_sql="""
                ALTER TABLE complaints_complaint
                ALTER COLUMN complaint_number
                DROP DEFAULT;
            """,
        ),
    ]
