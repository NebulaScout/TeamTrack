from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_delete_role'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE auth_user ADD CONSTRAINT unique_user_email UNIQUE (email);',
            reverse_sql='ALTER TABLE auth_user DROP CONSTRAINT unique_user_email;',
        ),
    ]