# Generated by Django 4.2.9 on 2024-01-16 23:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ifc_validation_models', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IfcAuthoringTool',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Authoring Tool (auto-generated).', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the Authoring Tool.', max_length=1024)),
                ('version', models.CharField(blank=True, help_text="Alphanumeric version of the Authoring Tool (eg. '1.0-alpha').", max_length=128, null=True)),
            ],
            options={
                'verbose_name': 'Authoring Tool',
                'verbose_name_plural': 'Authoring Tools',
                'db_table': 'ifc_authoring_tool',
            },
        ),
        migrations.CreateModel(
            name='IfcModel',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Model (auto-generated).', primary_key=True, serialize=False)),
                ('date', models.DateTimeField(help_text='Timestamp the Model was created.', null=True)),
                ('details', models.TextField(help_text='Details of the Model.', null=True)),
                ('file_name', models.CharField(help_text='Original name of the file that contained this Model.', max_length=1024)),
                ('file', models.CharField(help_text='File name as it stored.', max_length=1024)),
                ('size', models.PositiveIntegerField(help_text='Size of the model (bytes)')),
                ('hours', models.PositiveIntegerField(help_text='TBC (???)', null=True)),
                ('license', models.CharField(help_text='License of the Model.', max_length=7, null=True)),
                ('mvd', models.CharField(help_text='MVD Classification of the Model.', max_length=25, null=True)),
                ('number_of_elements', models.PositiveIntegerField(help_text='Number of elements within the Model.', null=True)),
                ('number_of_geometries', models.PositiveSmallIntegerField(help_text='Number of geometries within the Model.', null=True)),
                ('number_of_properties', models.PositiveSmallIntegerField(help_text='Number of properties within the Model.', null=True)),
                ('schema', models.CharField(help_text='Schema of the Model.', max_length=25, null=True)),
                ('status_bsdd', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the bSDD Validation.', max_length=1)),
                ('status_ia', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the IA Validation.', max_length=1)),
                ('status_ip', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the IP Validation.', max_length=1)),
                ('status_ids', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the IDS Validation.', max_length=1)),
                ('status_mvd', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the MVD Validation.', max_length=1)),
                ('status_schema', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the Schema Validation.', max_length=1)),
                ('status_syntax', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the Syntax Validation.', max_length=1)),
                ('status_industry_practices', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated')], db_index=True, default='n', help_text='Status of the Industry Practices Validation.', max_length=1)),
                ('properties', models.JSONField(help_text='Properties of the Model.', null=True)),
                ('created_by', models.ForeignKey(help_text='Who created this instance', on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('produced_by', models.ForeignKey(help_text='What tool was used to create this Model.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='models', to='ifc_validation_models.ifcauthoringtool')),
                ('updated_by', models.ForeignKey(help_text='Who updated this instance.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('uploaded_by', models.ForeignKey(help_text='Who uploaded this Model.', on_delete=django.db.models.deletion.RESTRICT, related_name='models', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Model',
                'verbose_name_plural': 'Models',
                'db_table': 'ifc_model',
            },
        ),
        migrations.AlterModelOptions(
            name='ifcgherkintaskresult',
            options={'verbose_name': 'Validation Gherkin Task Result', 'verbose_name_plural': 'Validation Gherkin Task Results'},
        ),
        migrations.AlterModelOptions(
            name='ifcvalidationrequest',
            options={'permissions': [('change_status', 'Can change status of Validation Request')], 'verbose_name': 'Validation Request', 'verbose_name_plural': 'Validation Requests'},
        ),
        migrations.AlterModelOptions(
            name='ifcvalidationtask',
            options={'verbose_name': 'Validation Task', 'verbose_name_plural': 'Validation Tasks'},
        ),
        migrations.AddField(
            model_name='ifcvalidationrequest',
            name='progress',
            field=models.PositiveSmallIntegerField(db_index=True, help_text='Overall progress (%) of the Validation Request.', null=True),
        ),
        migrations.AddField(
            model_name='ifcvalidationtask',
            name='progress',
            field=models.PositiveSmallIntegerField(db_index=True, help_text='Overall progress (%) of the Validation Task.', null=True),
        ),
        migrations.AlterField(
            model_name='ifcgherkintaskresult',
            name='request',
            field=models.ForeignKey(help_text='What Validation Request this Task belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='results', to='ifc_validation_models.ifcvalidationrequest'),
        ),
        migrations.AlterField(
            model_name='ifcgherkintaskresult',
            name='task',
            field=models.ForeignKey(help_text='What Validation Task this Result belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='results', to='ifc_validation_models.ifcvalidationtask'),
        ),
        migrations.AlterField(
            model_name='ifcvalidationrequest',
            name='id',
            field=models.AutoField(help_text='Identifier of the Validation Request (auto-generated).', primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='ifcvalidationrequest',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('INITIATED', 'Initiated'), ('FAILED', 'Failed'), ('COMPLETED', 'Completed')], db_index=True, default='PENDING', help_text='Current status of the Validation Request.', max_length=10),
        ),
        migrations.AlterField(
            model_name='ifcvalidationtask',
            name='ended',
            field=models.DateTimeField(db_index=True, help_text='Timestamp the Validation Task ended.', null=True, verbose_name='ended'),
        ),
        migrations.AlterField(
            model_name='ifcvalidationtask',
            name='request',
            field=models.ForeignKey(help_text='What Validation Request this Validation Task belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='ifc_validation_models.ifcvalidationrequest'),
        ),
        migrations.AlterField(
            model_name='ifcvalidationtask',
            name='started',
            field=models.DateTimeField(db_index=True, help_text='Timestamp the Validation Task was started.', null=True, verbose_name='started'),
        ),
        migrations.AlterField(
            model_name='ifcvalidationtask',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('SKIPPED', 'Skipped'), ('N/A', 'Not Applicable'), ('INITIATED', 'Initiated'), ('FAILED', 'Failed'), ('COMPLETED', 'Completed')], db_index=True, default='PENDING', help_text='Current status of the Validation Task.', max_length=15),
        ),
        migrations.AlterField(
            model_name='ifcvalidationtask',
            name='type',
            field=models.CharField(choices=[('SYNTAX', 'STEP Physical File Syntax'), ('SCHEMA', 'Schema (Express language)'), ('MVD', 'Model View Definitions'), ('BSDD', 'Requirements per bSDD Classification'), ('INFO', 'Parse Info'), ('PREREQ', 'Prerequisites'), ('NORMATIVE_IA', 'Normative Rules - Implementer Agreements (IA)'), ('NORMATIVE_IP', 'Gherkin Rules - Informal Propositions (IP)'), ('INDUSTRY', 'Industry Practices (TBC)')], db_index=True, help_text='Type of the Validation Task.', max_length=25),
        ),
        migrations.CreateModel(
            name='IfcModelInstance',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Model Instance (auto-generated).', primary_key=True, serialize=False)),
                ('stepfile_id', models.PositiveSmallIntegerField(db_index=True, help_text='TBC (???)')),
                ('ifc_type', models.CharField(db_index=True, help_text='IFC Type.', max_length=25)),
                ('fields', models.JSONField(help_text='Fields of the Instance.', null=True)),
                ('created_by', models.ForeignKey(help_text='Who created this instance', on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('model', models.ForeignKey(help_text='What Model this Model Instance is a part of.', on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='ifc_validation_models.ifcmodel')),
                ('updated_by', models.ForeignKey(help_text='Who updated this instance.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Model Instance',
                'verbose_name_plural': 'Model Instances',
                'db_table': 'ifc_model_instance',
            },
        ),
        migrations.CreateModel(
            name='IfcCompany',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Company (auto-generated).', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the Company.', max_length=1024, unique=True)),
                ('created_by', models.ForeignKey(help_text='Who created this instance', on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(help_text='Who updated this instance.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Company',
                'verbose_name_plural': 'Companies',
                'db_table': 'ifc_company',
            },
        ),
        migrations.AddField(
            model_name='ifcauthoringtool',
            name='company',
            field=models.ForeignKey(help_text='What Company this Authoring Tool belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='company', to='ifc_validation_models.ifccompany'),
        ),
        migrations.AddField(
            model_name='ifcauthoringtool',
            name='created_by',
            field=models.ForeignKey(help_text='Who created this instance', on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ifcauthoringtool',
            name='updated_by',
            field=models.ForeignKey(help_text='Who updated this instance.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='IfcValidationOutcome',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the validation outcome (auto-generated).', primary_key=True, serialize=False)),
                ('feature', models.CharField(help_text='Name of the Gherkin Feature.', max_length=1024)),
                ('feature_version', models.PositiveSmallIntegerField(db_index=True, help_text='Version number of the Gherkin Feature.')),
                ('code', models.CharField(db_index=True, help_text='Name of the Gherkin Feature.', max_length=6)),
                ('severity', models.PositiveSmallIntegerField(choices=[('1', 'Executed'), ('2', 'Passed'), ('3', 'Warning'), ('4', 'Error'), ('0', 'N/A')], db_index=True, default='0', help_text='Severity of the Validation Outcome.')),
                ('expected', models.JSONField(help_text='Expected value(s) for the Validation Outcome.', null=True)),
                ('observed', models.JSONField(help_text='Observed value(s) for the Validation Outcome.', null=True)),
                ('created_by', models.ForeignKey(help_text='Who created this instance', on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('instance', models.ForeignKey(help_text='What Model Instance this Outcome is applicable to.', on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='ifc_validation_models.ifcmodel')),
                ('updated_by', models.ForeignKey(help_text='Who updated this instance.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('validation_task', models.ForeignKey(help_text='What Validation Task this Outcome belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='ifc_validation_models.ifcvalidationtask')),
            ],
            options={
                'verbose_name': 'Validation Outcome',
                'verbose_name_plural': 'Validation Outcomes',
                'db_table': 'ifc_validation_outcome',
                'indexes': [models.Index(fields=['code', 'feature_version'], name='ifc_validat_code_b9df2a_idx'), models.Index(fields=['code', 'feature_version', 'severity'], name='ifc_validat_code_31150e_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='ifcauthoringtool',
            constraint=models.UniqueConstraint(fields=('name', 'version'), name='unique_name_version'),
        ),
    ]
