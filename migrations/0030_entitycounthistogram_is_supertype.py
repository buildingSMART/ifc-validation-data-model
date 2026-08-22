from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifc_validation_models", "0029_entitycounthistogram"),
    ]

    operations = [
        migrations.AddField(
            model_name="entitycounthistogram",
            name="is_supertype",
            field=models.BooleanField(
                db_index=True,
                default=None,
                help_text="Whether this count comes from instances of subtypes",
                null=True,
            ),
        ),
    ]
