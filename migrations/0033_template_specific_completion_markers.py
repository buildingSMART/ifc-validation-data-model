from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifc_validation_models", "0032_templatestatistic"),
    ]

    operations = [
        migrations.AlterField(
            model_name="templatestatistic",
            name="graph",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Bindings extracted from the template graph; null identifies a "
                    "completion marker for this template"
                ),
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="templatestatistic",
            name="template_name",
            field=models.CharField(
                help_text="Markdown template filename",
                max_length=255,
            ),
        ),
        migrations.AddConstraint(
            model_name="templatestatistic",
            constraint=models.UniqueConstraint(
                condition=models.Q(("graph__isnull", True)),
                fields=("model", "template_name"),
                name="unique_template_statistic_completion_marker",
            ),
        ),
    ]
