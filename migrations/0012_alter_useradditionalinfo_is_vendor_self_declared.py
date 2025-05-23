# Generated by Django 5.1.7 on 2025-03-17 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ifc_validation_models', '0011_useradditionalinfo_is_vendor_self_declared'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useradditionalinfo',
            name='is_vendor_self_declared',
            field=models.BooleanField(blank=True, help_text='Whether this user has self-declared an affiliation with an Authoring Tool vendor (optional)', null=True, verbose_name='is vendor (self declared)'),
        ),
    ]
