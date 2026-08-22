import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifc_validation_models", "0031_psetcounthistogram"),
    ]

    operations = [
        migrations.CreateModel(
            name="TemplateStatistic",
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
                    "template_name",
                    models.CharField(
                        blank=True,
                        help_text="Markdown template name; blank identifies the completion marker",
                        max_length=255,
                    ),
                ),
                (
                    "graph",
                    models.JSONField(
                        default=dict,
                        help_text="Bindings extracted from the template graph",
                    ),
                ),
                (
                    "focus_instance",
                    models.ForeignKey(
                        help_text="Focus instance matched by the template",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="template_statistics",
                        to="ifc_validation_models.modelinstance",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        help_text="Model for which the template statistics were computed",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="template_statistics",
                        to="ifc_validation_models.model",
                    ),
                ),
            ],
        ),
    ]
