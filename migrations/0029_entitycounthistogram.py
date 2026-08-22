import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifc_validation_models", "0028_alter_whitelistentry_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="EntityCountHistogram",
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
                        help_text="Index into sorted entity names from the schema in model the associated model"
                    ),
                ),
                (
                    "count",
                    models.PositiveIntegerField(help_text="Size of the model (bytes)"),
                ),
                (
                    "model",
                    models.ForeignKey(
                        help_text="Owning model of this histogram entry",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="histogram_entries",
                        to="ifc_validation_models.model",
                    ),
                ),
            ],
        ),
    ]
