"""Expression indexes for template graph values.

Both indexes are partial (one template each) and cover the columns the
statistics query builder needs, so PostgreSQL can plan bitmap or index-only
scans without reading the JSON payload of every row.
"""

from django.db import migrations, models
from django.db.models.fields.json import KeyTextTransform


# Written as raw SQL: the DDL already exists on the long-lived deployments
# (created out of band), so plain CREATE INDEX IF NOT EXISTS keeps the
# container startup migration a no-op there.
CREATE_PROPERTY_INDEX = (
    "CREATE INDEX IF NOT EXISTS templatestat_propertytype_idx "
    "ON ifc_validation_models_templatestatistic USING btree "
    "((graph ->> 'PropertyType')) INCLUDE (id, model_id) "
    "WHERE template_name = 'Use_of_property_types.md'"
)
CREATE_PARENT_CURVE_INDEX = (
    "CREATE INDEX IF NOT EXISTS templatestat_parentcurve_idx "
    "ON ifc_validation_models_templatestatistic USING btree "
    "((graph ->> 'ParentCurve')) INCLUDE (id, model_id) "
    "WHERE template_name = 'Usage_of_transition_curves_geometry.md'"
)


def create_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(CREATE_PROPERTY_INDEX)
    schema_editor.execute(CREATE_PARENT_CURVE_INDEX)


def drop_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP INDEX IF EXISTS templatestat_propertytype_idx")
    schema_editor.execute("DROP INDEX IF EXISTS templatestat_parentcurve_idx")


class Migration(migrations.Migration):

    dependencies = [
        ("ifc_validation_models", "0035_authoring_tool_language_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name="templatestatistic",
                    index=models.Index(
                        KeyTextTransform("PropertyType", "graph"),
                        condition=models.Q(template_name="Use_of_property_types.md"),
                        include=("id", "model_id"),
                        name="templatestat_propertytype_idx",
                    ),
                ),
                migrations.AddIndex(
                    model_name="templatestatistic",
                    index=models.Index(
                        KeyTextTransform("ParentCurve", "graph"),
                        condition=models.Q(
                            template_name="Usage_of_transition_curves_geometry.md",
                        ),
                        include=("id", "model_id"),
                        name="templatestat_parentcurve_idx",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(create_indexes, drop_indexes),
            ],
        ),
    ]
