from django.db import migrations, models

from apps.ifc_validation_models.languages import backfill_authoring_tools


def backfill_language_fields(apps, schema_editor):

    AuthoringTool = apps.get_model("ifc_validation_models", "AuthoringTool")
    backfill_authoring_tools(AuthoringTool)


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
                db_index=True,
                default="",
                help_text="Language-neutral name of the Authoring Tool, eg. 'Revit 26.4.0.32' for 'Revit 26.4.0.32 (ENU)'. Derived from name on save; equals name when no language package marker was recognized.",
                max_length=1024,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="authoringtool",
            name="language_code",
            field=models.CharField(
                blank=True,
                help_text="Normalized language code of the Authoring Tool's language package, derived from name on save: ISO 639-1 where possible ('en' for '(ENU)'), with a script subtag where needed ('zh-hans'/'zh-hant'). NULL when no language package marker was recognized.",
                max_length=16,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_language_fields, migrations.RunPython.noop),
    ]
