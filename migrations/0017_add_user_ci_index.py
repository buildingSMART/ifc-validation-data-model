from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ifc_validation_models', '0016_alter_validationrequest_channel'),
    ]

    operations = [
        # '__iexact=' typically translates to UPPER(...) = UPPER(...) in SQL
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS auth_user_username_ci_idx ON auth_user (upper(username));",
            reverse_sql="DROP INDEX IF EXISTS auth_user_username_ci_idx;",
        )
    ]