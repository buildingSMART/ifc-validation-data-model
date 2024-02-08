# Generated by Django 4.2.9 on 2024-02-01 15:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthoringTool',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
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
            name='Company',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Company (auto-generated).', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the Company.', max_length=1024, unique=True)),
            ],
            options={
                'verbose_name': 'Company',
                'verbose_name_plural': 'Companies',
                'db_table': 'ifc_company',
            },
        ),
        migrations.CreateModel(
            name='Model',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Model (auto-generated).', primary_key=True, serialize=False)),
                ('date', models.DateTimeField(blank=True, help_text='Timestamp the Model was created.', null=True)),
                ('details', models.TextField(blank=True, help_text='Details of the Model.', null=True)),
                ('file_name', models.CharField(help_text='Original name of the file that contained this Model.', max_length=1024)),
                ('file', models.CharField(help_text='File name as it stored.', max_length=1024)),
                ('size', models.PositiveIntegerField(help_text='Size of the model (bytes)')),
                ('hours', models.PositiveIntegerField(blank=True, help_text='TBC (???)', null=True)),
                ('license', models.CharField(choices=[('UNKNOWN', 'Unknown'), ('PRIVATE', 'Private'), ('CC', 'CC'), ('MIT', 'MIT'), ('GPL', 'GPL'), ('LGPL', 'LGPL')], db_index=True, default='UNKNOWN', help_text='License of the Model.', max_length=7)),
                ('mvd', models.CharField(blank=True, help_text='MVD Classification of the Model.', max_length=150, null=True)),
                ('number_of_elements', models.PositiveIntegerField(blank=True, help_text='Number of elements within the Model.', null=True)),
                ('number_of_geometries', models.PositiveIntegerField(blank=True, help_text='Number of geometries within the Model.', null=True)),
                ('number_of_properties', models.PositiveIntegerField(blank=True, help_text='Number of properties within the Model.', null=True)),
                ('schema', models.CharField(blank=True, help_text='Schema of the Model.', max_length=25, null=True)),
                ('status_bsdd', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the bSDD Validation.', max_length=1)),
                ('status_ia', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the IA Validation.', max_length=1)),
                ('status_ip', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the IP Validation.', max_length=1)),
                ('status_ids', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the IDS Validation.', max_length=1)),
                ('status_mvd', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the MVD Validation.', max_length=1)),
                ('status_schema', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the Schema Validation.', max_length=1)),
                ('status_syntax', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the Syntax Validation.', max_length=1)),
                ('status_industry_practices', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the Industry Practices Validation.', max_length=1)),
                ('status_prereq', models.CharField(choices=[('v', 'Valid'), ('i', 'Invalid'), ('n', 'Not Validated'), ('w', 'Warning'), ('-', 'Not Applicable')], db_index=True, default='n', help_text='Status of the Prerequisites Validation.', max_length=1)),
                ('properties', models.JSONField(blank=True, help_text='Properties of the Model.', null=True)),
                ('produced_by', models.ForeignKey(blank=True, help_text='What tool was used to create this Model.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='models', to='ifc_validation_models.authoringtool')),
                ('uploaded_by', models.ForeignKey(help_text='Who uploaded this Model.', on_delete=django.db.models.deletion.RESTRICT, related_name='models', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Model',
                'verbose_name_plural': 'Models',
                'db_table': 'ifc_model',
            },
        ),
        migrations.CreateModel(
            name='ModelInstance',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Model Instance (auto-generated).', primary_key=True, serialize=False)),
                ('stepfile_id', models.PositiveBigIntegerField(db_index=True, help_text='id assigned within the Step File (eg. #11)')),
                ('ifc_type', models.CharField(db_index=True, help_text='IFC Type.', max_length=50)),
                ('fields', models.JSONField(blank=True, help_text='Fields of the Instance.', null=True)),
                ('model', models.ForeignKey(help_text='What Model this Model Instance is a part of.', on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='ifc_validation_models.model')),
            ],
            options={
                'verbose_name': 'Model Instance',
                'verbose_name_plural': 'Model Instances',
                'db_table': 'ifc_model_instance',
            },
        ),
        migrations.CreateModel(
            name='ValidationRequest',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Validation Request (auto-generated).', primary_key=True, serialize=False)),
                ('file_name', models.CharField(help_text='Name of the file.', max_length=1024, verbose_name='file name')),
                ('file', models.FileField(help_text='Path of the file.', upload_to='')),
                ('size', models.PositiveIntegerField(help_text='Size of the file (bytes)')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('INITIATED', 'Initiated'), ('FAILED', 'Failed'), ('COMPLETED', 'Completed')], db_index=True, default='PENDING', help_text='Current status of the Validation Request.', max_length=10)),
                ('status_reason', models.TextField(blank=True, help_text='Reason for current status.', null=True)),
                ('started', models.DateTimeField(db_index=True, help_text='Timestamp the Validation Request was started.', null=True, verbose_name='started')),
                ('completed', models.DateTimeField(db_index=True, help_text='Timestamp the Validation Request completed.', null=True, verbose_name='completed')),
                ('progress', models.PositiveSmallIntegerField(blank=True, db_index=True, help_text='Overall progress (%) of the Validation Request.', null=True)),
                ('created_by', models.ForeignKey(help_text='Who created this instance', on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('model', models.OneToOneField(help_text='What Model is created based on this Validation Request.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='request', to='ifc_validation_models.model')),
                ('updated_by', models.ForeignKey(blank=True, help_text='Who updated this instance.', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Validation Request',
                'verbose_name_plural': 'Validation Requests',
                'db_table': 'ifc_validation_request',
                'permissions': [('change_status', 'Can change status of Validation Request')],
            },
        ),
        migrations.CreateModel(
            name='ValidationTask',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the task (auto-generated).', primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('SYNTAX', 'STEP Physical File Syntax'), ('SCHEMA', 'Schema (EXPRESS language)'), ('MVD', 'Model View Definitions'), ('BSDD', 'bSDD Compliance'), ('INFO', 'Parse Info'), ('PREREQ', 'Prerequisites'), ('NORMATIVE_IA', 'Implementer Agreements (IA)'), ('NORMATIVE_IP', 'Informal Propositions (IP)'), ('INDUSTRY', 'Industry Practices')], db_index=True, help_text='Type of the Validation Task.', max_length=25)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SKIPPED', 'Skipped'), ('N/A', 'Not Applicable'), ('INITIATED', 'Initiated'), ('FAILED', 'Failed'), ('COMPLETED', 'Completed')], db_index=True, default='PENDING', help_text='Current status of the Validation Task.', max_length=15)),
                ('status_reason', models.TextField(blank=True, help_text='Reason for current status.', null=True)),
                ('started', models.DateTimeField(db_index=True, help_text='Timestamp the Validation Task was started.', null=True, verbose_name='started')),
                ('ended', models.DateTimeField(db_index=True, help_text='Timestamp the Validation Task ended.', null=True, verbose_name='ended')),
                ('progress', models.PositiveSmallIntegerField(blank=True, db_index=True, help_text='Overall progress (%) of the Validation Task.', null=True)),
                ('process_id', models.PositiveIntegerField(blank=True, help_text='Process id of subprocess executing the Validation Task.', null=True)),
                ('process_cmd', models.TextField(blank=True, help_text='Command and arguments used to launch the subprocess executing the Validation Task.', null=True)),
                ('request', models.ForeignKey(help_text='What Validation Request this Validation Task belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='ifc_validation_models.validationrequest')),
            ],
            options={
                'verbose_name': 'Validation Task',
                'verbose_name_plural': 'Validation Tasks',
                'db_table': 'ifc_validation_task',
            },
        ),
        migrations.CreateModel(
            name='ValidationOutcome',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, help_text='Timestamp this instance was created.')),
                ('updated', models.DateTimeField(blank=True, help_text='Timestamp this instance was last updated.', null=True)),
                ('id', models.AutoField(help_text='Identifier of the Validation Outcome (auto-generated).', primary_key=True, serialize=False)),
                ('feature', models.CharField(blank=True, help_text='Name of the Gherkin Feature (optional).', max_length=1024, null=True)),
                ('feature_version', models.PositiveSmallIntegerField(blank=True, db_index=True, help_text='Version number of the Gherkin Feature (optional).', null=True)),
                ('severity', models.PositiveSmallIntegerField(choices=[(1, 'Executed'), (2, 'Passed'), (3, 'Warning'), (4, 'Error'), (0, 'N/A')], db_index=True, default=0, help_text='Severity of the Validation Outcome.')),
                ('outcome_code', models.CharField(choices=[('P00010', 'Passed'), ('N00010', 'Not Applicable'), ('E00001', 'Syntax Error'), ('E00002', 'Schema Error'), ('E00010', 'Type Error'), ('E00020', 'Value Error'), ('E00030', 'Geometry Error'), ('E00040', 'Cardinality Error'), ('E00050', 'Duplicate Error'), ('E00060', 'Placement Error'), ('E00070', 'Units Error'), ('E00080', 'Quantity Error'), ('E00090', 'Enumerated Value Error'), ('E00100', 'Relationship Error'), ('E00110', 'Naming Error'), ('E00120', 'Reference Error'), ('E00130', 'Resource Error'), ('E00140', 'Deprecation Error'), ('E00150', 'Shape Representation Error'), ('E00160', 'Instance Structure Error'), ('W00010', 'Alignment Contains Business Logic Only'), ('W00020', 'Alignment Contains Geometry Only'), ('W00030', 'Warning'), ('X00040', 'Executed')], default='N00010', help_text='Code representing the Validation Outcome.', max_length=10)),
                ('expected', models.JSONField(blank=True, help_text='Expected value(s) for the Validation Outcome.', null=True)),
                ('observed', models.JSONField(blank=True, help_text='Observed value(s) for the Validation Outcome.', null=True)),
                ('instance', models.ForeignKey(help_text='What Model Instance this Outcome is applicable to (optional).', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='ifc_validation_models.modelinstance')),
                ('validation_task', models.ForeignKey(help_text='What Validation Task this Outcome belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='ifc_validation_models.validationtask')),
            ],
            options={
                'verbose_name': 'Validation Outcome',
                'verbose_name_plural': 'Validation Outcomes',
                'db_table': 'ifc_validation_outcome',
            },
        ),
        migrations.AddField(
            model_name='authoringtool',
            name='company',
            field=models.ForeignKey(blank=True, help_text='What Company this Authoring Tool belongs to (optional).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company', to='ifc_validation_models.company'),
        ),
        migrations.AddIndex(
            model_name='validationrequest',
            index=models.Index(fields=['file_name', 'status'], name='ifc_validat_file_na_442c43_idx'),
        ),
        migrations.AddIndex(
            model_name='validationoutcome',
            index=models.Index(fields=['feature', 'feature_version'], name='ifc_validat_feature_5ffe39_idx'),
        ),
        migrations.AddIndex(
            model_name='validationoutcome',
            index=models.Index(fields=['feature', 'feature_version', 'severity'], name='ifc_validat_feature_2540c6_idx'),
        ),
        migrations.AddConstraint(
            model_name='authoringtool',
            constraint=models.UniqueConstraint(fields=('name', 'version'), name='unique_name_version'),
        ),
    ]
