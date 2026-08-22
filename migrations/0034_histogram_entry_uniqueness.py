from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "ifc_validation_models",
            "0033_template_specific_completion_markers",
        ),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="entitycounthistogram",
            constraint=models.UniqueConstraint(
                fields=("model", "entity_index", "is_supertype"),
                name="unique_entity_histogram_entry",
            ),
        ),
        migrations.AddConstraint(
            model_name="psetcounthistogram",
            constraint=models.UniqueConstraint(
                fields=("model", "entity_index", "pset_name"),
                name="unique_pset_histogram_entry",
            ),
        ),
    ]
