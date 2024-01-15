# IFC Validation Models

Django app and model for IFC Validation Service entities

## Entities

- IFC Validation Request
- IFC Validation Task

## How to run?

### Initial run

Add this folder as a submodule to the 'apps' folder of your Django project.

Next, run these commands to configure Django for initial run.

```shell
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser --username SYSTEM
```

### Unit Test

```shell
python3 manage.py test apps --settings apps.ifc_validation_models.test_settings --debug-mode --verbosity 3
```