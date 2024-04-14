# IFC Validation Models

Django app and model for IFC Validation Service entities

## Entities

- Company
- Authoring Tool
- Model
- Model Instance
- Validation Request
- Validation Task
- Validation Outcome

## How to run?

### Initial run

Add this folder as a submodule to the 'apps' folder of your Django project.

Next, run these commands to configure Django for initial run.

```shell
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser --username SYSTEM
```

### Integration Tests

Run this command to run tests against in-memory database.

```shell
python3 manage.py test apps --settings apps.ifc_validation_models.test_settings --debug-mode --verbosity 3
```

### Usage as a datamodel independent of django app

Clone this repository as a submodule directory named `ifc_validation_models`. This name has to match as it is the name of the app and has to be importable under this path.

```python
import os

import django
from django.core.management import call_command

# monkey patch the name, because we don't have an `apps` folder
import ifc_validation_models.apps
ifc_validation_models.apps.IfcValidationModelsConfig.name = 'ifc_validation_models'

os.environ['DJANGO_SETTINGS_MODULE'] = 'ifc_validation_models.independent_worker_settings'

# Setup, initialize db and perform migration
django.setup()
call_command(
    'migrate', interactive=False,
)

import ifc_validation_models.models as database
from django.contrib.auth.models import User

# Create a mandatory user and assign to context
user = User.objects.create_user(username='Thomas',
                                 email='tk@aecgeeks.com',
                                 password='something funky')
database.set_user_context(user)

# Interact with the datamodel
model = database.IfcModel.objects.create(
    size=1,
    uploaded_by = user
)

instance = database.IfcModelInstance.objects.create(
    stepfile_id=1,
    model = model
)

database.IfcValidationOutcome.objects.create(
    feature_version=1,
    instance=instance
)
```
