from django.db import migrations, models

from apps.ifc_validation_models.languages import backfill_authoring_tools


def backfill_language_fields(apps, schema_editor):

    AuthoringTool = apps.get_model("ifc_validation_models", "AuthoringTool")
    backfill_authoring_tools(AuthoringTool)


def clear_language_fields(apps, schema_editor):

    AuthoringTool = apps.get_model("ifc_validation_models", "AuthoringTool")
    AuthoringTool.objects.update(canonical_name=None, language_code=None)


class Migration(migrations.Migration):

    dependencies = [
        (
            "ifc_validation_models",
            "0034_histogram_entry_uniqueness",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="authoringtool",
            name="canonical_name",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Language-neutral name of the Authoring Tool, eg. 'Revit 26.4.0.32' for 'Revit 26.4.0.32 (ENU)'. Equals name when no language package marker was recognized.",
                max_length=1024,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="authoringtool",
            name="language_code",
            field=models.CharField(
                blank=True,
                help_text="Normalized language code of the Authoring Tool's language package, eg. 'en' for '(ENU)' (optional).",
                max_length=16,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_language_fields, clear_language_fields),
    ]
