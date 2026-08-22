import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifc_validation_models", "0030_entitycounthistogram_is_supertype"),
    ]

    operations = [
        migrations.CreateModel(
            name="PsetCountHistogram",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "entity_index",
                    models.PositiveIntegerField(
                        help_text="Index into sorted entity names from the schema of the associated model",
                        null=True,
                    ),
                ),
                (
                    "pset_name",
                    models.CharField(
                        blank=True,
                        help_text="Name of the property definition",
                        max_length=1024,
                    ),
                ),
                (
                    "is_standardized",
                    models.BooleanField(
                        db_index=True,
                        help_text="Whether the property definition is standardized for the IFC schema",
                    ),
                ),
                (
                    "count",
                    models.PositiveIntegerField(
                        help_text="Number of property definitions or related objects"
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        help_text="Owning model of this histogram entry",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pset_count_entries",
                        to="ifc_validation_models.model",
                    ),
                ),
            ],
        ),
    ]
