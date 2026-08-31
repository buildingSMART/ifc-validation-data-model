from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from apps.ifc_validation_models.models import ValidationRequest, ValidationTask  # TODO: for now needs to be absolute!
from apps.ifc_validation_models.models import Company, AuthoringTool, Model
from apps.ifc_validation_models.models import UserAdditionalInfo
from apps.ifc_validation_models.models import ValidationOutcome
from apps.ifc_validation_models.models import set_user_context

class ValidationModelsTestCase(TestCase):

    def set_user_context():
        user, _ = User.objects.get_or_create(id=1, defaults={'username': 'SYSTEM', 'is_active': True})
        set_user_context(user)

    def test_created_request_has_status_pending(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test.ifc',
            file='test.ifc', 
            size=1024
        )

        # act
        request2 = ValidationRequest.objects.get(id=request.id)

        # assert
        self.assertEqual(request2.status, ValidationRequest.Status.PENDING)

    def test_created_request_has_channel_api(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test.ifc',
            file='test.ifc',
            size=1024
        )

        # act
        request2 = ValidationRequest.objects.get(id=request.id)

        # assert
        self.assertEqual(request2.channel, ValidationRequest.Channel.API)

    def test_created_request_has_created_fields(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test2.ifc',
            file='test2.ifc', 
            size=1024
        )

        # act
        request2 = ValidationRequest.objects.get(id=request.id)

        # assert
        self.assertIsNotNone(request2.created)
        self.assertEqual(request2.created_by.username, 'SYSTEM')
        self.assertEqual(request2.created_by.id, 1)
        self.assertIsNone(request2.updated)
        self.assertIsNone(request2.updated_by)

    def test_updated_request_has_updated_fields(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test3.ifc',
            file='test3.ifc',
            size=1024
        )

        # act
        request2 = ValidationRequest.objects.get(id=request.id)
        request2.save()  # simulate update

        # assert
        self.assertIsNotNone(request2.created)
        self.assertEqual(request2.created_by.username, 'SYSTEM')
        self.assertEqual(request2.created_by.id, 1)
        self.assertIsNotNone(request2.created)
        self.assertEqual(request2.updated_by.username, 'SYSTEM')
        self.assertEqual(request2.updated_by.id, 1)

    def test_created_task_has_status_pending(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test4.ifc',
            file='test4.ifc',
            size=1024
        )

        # act
        task = ValidationTask.objects.create(
            request=request
        )

        task2 = ValidationTask.objects.get(id=task.id)

        # assert
        self.assertEqual(task2.status, ValidationTask.Status.PENDING)

    def test_created_tasks_can_be_navigated(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(file_name='test5.ifc', file='test5.ifc', size=1024)
        task1 = ValidationTask.objects.create(request=request)
        task2 = ValidationTask.objects.create(request=request)
        task3 = ValidationTask.objects.create(request=request)

        request2 = ValidationRequest.objects.create(file_name='test6.ifc', file='test6.ifc', size=1024)
        ValidationTask.objects.create(request=request2)
        ValidationTask.objects.create(request=request2)

        # act
        all_tasks = ValidationTask.objects.all()
        tasks = ValidationTask.objects.filter(request__id=request.id)

        # assert
        self.assertEqual(all_tasks.count(), 5)
        self.assertEqual(tasks.count(), 3)
        self.assertEqual(task1.id, tasks[0].id)
        self.assertEqual(task2.id, tasks[1].id)
        self.assertEqual(task3.id, tasks[2].id)

    def test_newly_created_tool_and_model_can_be_navigated(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        user = User.objects.get(id=1)
        company = Company.objects.create(name='Acme Inc.')
        tool = AuthoringTool.objects.create(name='Tool XYZ', version='1.0-alpha', company=company)
        model = Model.objects.create(file_name='test_123.ifc', size=2048, produced_by=tool, uploaded_by=user)
        model2 = Model.objects.create(file_name='test_xyz.ifc', size=4096, produced_by=tool, uploaded_by=user)

        # act
        all_tools = AuthoringTool.objects.all()

        # assert
        self.assertEqual(all_tools.count(), 1)
        self.assertEqual(all_tools[0].id, tool.id)
        self.assertEqual(tool.company.name, company.name)
        self.assertEqual(all_tools[0].company.name, company.name)
        self.assertEqual(model.produced_by.company.name, company.name)
        self.assertEqual(model.uploaded_by.username, user.username)
        self.assertEqual(user.models.count(), 2)
        self.assertEqual(user.models.all()[1].file_name, model2.file_name)

    def test_find_tool_by_full_name_should_succeed(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company1 = Company.objects.create(name='Acme Inc.')
        tool1 = AuthoringTool.objects.create(name='Tool ABC', version='1.0', company=company1)
        tool2 = AuthoringTool.objects.create(name='Tool ABC', version='2.0-alpha', company=company1)

        company2 = Company.objects.create(name='PyCAD Limited')
        tool3 = AuthoringTool.objects.create(name='App', version=None, company=company2)
        tool4 = AuthoringTool.objects.create(name='App', version='2024', company=company2)

        # act/assert
        name_to_find = 'Acme Inc. - Tool ABC - 1.0'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)
        self.assertEqual(found_tool.company.name, tool1.company.name)

        name_to_find = 'Acme Inc. - Tool ABC 1.0'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)
        self.assertEqual(found_tool.company.name, tool1.company.name)

        name_to_find = 'PyCAD Limited'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNone(found_tool)

        name_to_find = 'PyCAD Limited App'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool3.name)
        self.assertEqual(found_tool.company.name, tool3.company.name)

        name_to_find = 'PyCAD Limited - App 2024'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool4.name)
        self.assertEqual(found_tool.company.name, tool4.company.name)

        name_to_find = 'PyCAD Limited App 2020'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNone(found_tool)

    def test_find_tool_by_full_name_should_succeed2(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        tool1 = AuthoringTool.objects.create(name='Test Application', version='0.10')        
        tool2 = AuthoringTool.objects.create(name='Test Application', version='2023-01')        

        # act/assert
        name_to_find = 'Test Application - 0.10'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)
        self.assertIsNone(found_tool.company)
        
        name_to_find = 'Test Application - 2023-01'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool2.name)
        self.assertIsNone(found_tool.company)

    def test_find_tool_by_full_name_should_succeed3(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        tool1 = AuthoringTool.objects.create(name='IfcOpenShell-v0.7.0-6c9e130ca', version='v0.7.0-6c9e130ca')        

        # act
        name_to_find = 'IfcOpenShell-v0.7.0-6c9e130ca v0.7.0-6c9e130ca'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)

        # assert
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)
        self.assertIsNone(found_tool.company)

    def test_find_tool_by_full_name_should_succeed4(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        tool1 = AuthoringTool.objects.create(name='MyFabTool', version='1.0')

        # act
        name_to_find = 'MyFabTool - 1.0'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)

        # assert
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)
        self.assertIsNone(found_tool.company)

    def test_find_tool_by_full_name_should_return_none(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        AuthoringTool.objects.create(name='Test Application', version='0.10')        

        # act
        name_to_find = 'Test Application 0.12'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)

        # assert
        self.assertIsNone(found_tool)

    def test_add_tool_twice_should_fail(self):

        # arrange
        ValidationModelsTestCase.set_user_context()        

        # act/assert
        AuthoringTool.objects.create(name='Test Application', version='0.10') # should succeed
        AuthoringTool.objects.create(name='Test Application', version='0.11') # should succeed
        with self.assertRaises(IntegrityError):
            AuthoringTool.objects.create(name='Test Application', version='0.11') # should fail

    def test_add_tool_with_company_twice_should_fail(self):

        # arrange
        ValidationModelsTestCase.set_user_context()

        # act/assert
        company, _ = Company.objects.get_or_create(name='Acme Inc.')
        AuthoringTool.objects.create(name='Test Application', version='0.10', company=company) # should succeed
        AuthoringTool.objects.create(name='Test Application', version='0.11', company=company) # should succeed
        with self.assertRaises(IntegrityError):
            AuthoringTool.objects.create(name='Test Application', version='0.11', company=company) # should fail

    def test_model_can_navigate_back_to_request(self):
        
        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test.ifc', 
            file='test.ifc', 
            size=1024
        )
        
        model, _ =  Model.objects.get_or_create(
            file_name = request.file_name,
            file = request.file,
            size = 0,
            uploaded_by = request.created_by
        )
        request.model = model
        request.save()

        # act
        request2 = ValidationRequest.objects.get(id=request.id)
        
        # assert
        self.assertIsNotNone(request2.model)
        self.assertEqual(request.id, model.request.id)
        self.assertEqual(request2.id, model.request.id)

    def test_task_can_navigate_back_to_model(self):
        
        # arrange
        ValidationModelsTestCase.set_user_context()
        request = ValidationRequest.objects.create(
            file_name='test.ifc', 
            file='test.ifc', 
            size=1024
        )        
        task = ValidationTask.objects.create(
            request=request, 
            type=ValidationTask.Type.HEADER
        )
        model, _ =  Model.objects.get_or_create(
            file_name = request.file_name,
            file = request.file,
            size = request.size,
            uploaded_by = request.created_by
        )
        request.model = model
        request.save()

        # act
        retrieved_task = ValidationTask.objects.get(id=task.id)
        retrieved_model = retrieved_task.request.model
        model_id = retrieved_model.id

        # assert
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(model.id, model_id)

    def test_find_users_by_email_pattern_should_succeed(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company = Company.objects.create(name='Acme Inc.', email_address_pattern='@acme.com')
        user1 = User.objects.create(id=2, username='JohnDoe', email='jdoe@acme.com', is_active=True)
        user2 = User.objects.create(id=3, username='JaneDoe', email='jane@looneytunes.com', is_active=True)

        # act
        users = company.find_users_by_email_pattern()

        # assert
        self.assertIsNotNone(users)
        self.assertEqual(1, len(users))
        self.assertEqual(user1, users[0])

    def test_find_users_by_email_pattern_should_succeed2(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company = Company.objects.create(name='Acme Inc.', email_address_pattern='@acme.com')
        user1 = User.objects.create(id=2, username='JohnDoe', email='jdoe@acme.com', is_active=True)
        uai1 = UserAdditionalInfo.objects.create(user=user1, company=company)
        user2 = User.objects.create(id=3, username='JaneDoe', email='jane@acme.com', is_active=True)

        # act
        users = company.find_users_by_email_pattern(only_new=True)

        # assert
        self.assertIsNotNone(users)
        self.assertEqual(1, len(users))
        self.assertEqual(user2, users[0])

    def test_find_users_by_email_pattern_should_return_none(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company = Company.objects.create(name='Acme Inc.', email_address_pattern='@acme.com')
        user1 = User.objects.create(id=2, username='JohnDoe', email='jdoe@protonmail.com', is_active=True)
        user2 = User.objects.create(id=3, username='JaneDoe', email='jane@looneytunes.com', is_active=True)

        # act
        users = company.find_users_by_email_pattern()

        # assert
        self.assertIsNone(users)

    def test_find_company_by_email_pattern_should_succeed(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company = Company.objects.create(name='Acme Inc.', email_address_pattern='@acme.com|@looneytunes.com')
        user1 = User.objects.create(id=2, username='JohnDoe', email='jdoe@acme.com', is_active=True)
        user2 = User.objects.create(id=3, username='JaneDoe', email='jane@looneytunes.com', is_active=True)

        # act
        company1 = UserAdditionalInfo.find_company_by_email_pattern(user1)
        company2 = UserAdditionalInfo.find_company_by_email_pattern(user2)

        # assert
        self.assertIsNotNone(company1)
        self.assertIsNotNone(company2)
        self.assertEqual(company, company1)
        self.assertEqual(company, company2)

    def test_find_company_by_email_pattern_should_succeed2(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company = Company.objects.create(name='Acme Inc.', email_address_pattern='@acme.com')
        user1 = User.objects.create(id=2, username='JohnDoe', email='jdoe@acme.com', is_active=True)
        user2 = User.objects.create(id=3, username='JaneDoe', email='jane@looneytunes.com', is_active=True)

        # act
        company1 = UserAdditionalInfo.find_company_by_email_pattern(user1)
        company2 = UserAdditionalInfo.find_company_by_email_pattern(user2)

        # assert
        self.assertIsNotNone(company1)
        self.assertIsNone(company2)
        self.assertEqual(company, company1)

    def test_find_company_by_email_pattern_should_return_none(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        company = Company.objects.create(name='Acme Inc.', email_address_pattern='@acme.com')
        user1 = User.objects.create(id=2, username='JohnDoe', email='jdoe@protonmail.com', is_active=True)
        user2 = User.objects.create(id=3, username='JaneDoe', email='jane@looneytunes.com', is_active=True)

        # act
        company1 = UserAdditionalInfo.find_company_by_email_pattern(user1)
        company2 = UserAdditionalInfo.find_company_by_email_pattern(user2)

        # assert
        self.assertIsNone(company1)
        self.assertIsNone(company2)
    
    def test_find_user_by_username_should_succeed(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        user = User.objects.create(id=2, username='JohnDoe', email='jdoe@acme.com', is_active=True)

        # act
        result = UserAdditionalInfo.find_user_by_username('johndoe') # notice: all lower case
        result2 = UserAdditionalInfo.find_user_by_username('JOHNDOE') # notice: all upper case

        # assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result2)
        self.assertEqual(user, result)
        self.assertEqual(user, result2)

    def test_find_user_by_username_should_return_none(self):

        # arrange
        ValidationModelsTestCase.set_user_context()
        user = User.objects.create(id=2, username='JohnDoe', email='jdoe@acme.com', is_active=True)

        # act
        result = UserAdditionalInfo.find_user_by_username('jane')

        # assert
        self.assertIsNone(result)


class AggregateStatusTestCase(TestCase):
    """A task / category with NO outcomes (skipped or never-run) must aggregate to
    NOT_VALIDATED, not VALID — otherwise a skipped check shows a green checkmark.
    Covers both the Python (determine_aggregate_status) and SQL (with_aggregate_status)
    paths and the *_calculated properties the UI reads."""

    S = ValidationOutcome.OutcomeSeverity
    T = ValidationTask.Type
    St = Model.Status

    @staticmethod
    def set_user_context():
        user, _ = User.objects.get_or_create(id=1, defaults={'username': 'SYSTEM', 'is_active': True})
        set_user_context(user)
        return user

    def _task_with(self, severities, type=None, request=None):
        if request is None:
            request = ValidationRequest.objects.create(file_name='a.ifc', file='a.ifc', size=0)
            request.mark_as_initiated()
        task = ValidationTask.objects.create(request=request, type=type or self.T.SCHEMA)
        for sev in severities:
            ValidationOutcome.objects.create(validation_task=task, severity=sev)
        return task

    def _model_with_task(self, ttype, severities):
        user = self.set_user_context()
        model = Model.objects.create(file_name='m.ifc', size=1, uploaded_by=user)
        request = ValidationRequest.objects.create(file_name='m.ifc', file='m.ifc', size=1)
        request.model = model
        request.save()
        self._task_with(severities, type=ttype, request=request)
        return Model.objects.get(id=model.id)

    # ---- Layer 1: determine_aggregate_status() (Python) ----
    def test_determine_aggregate_status_no_outcomes_is_not_validated(self):
        self.set_user_context()
        self.assertEqual(self._task_with([]).determine_aggregate_status(), self.St.NOT_VALIDATED)

    def test_determine_aggregate_status_executed_is_valid(self):
        self.set_user_context()
        self.assertEqual(self._task_with([self.S.EXECUTED, self.S.PASSED]).determine_aggregate_status(), self.St.VALID)

    def test_determine_aggregate_status_error_is_invalid(self):
        self.set_user_context()
        self.assertEqual(self._task_with([self.S.PASSED, self.S.ERROR]).determine_aggregate_status(), self.St.INVALID)

    def test_determine_aggregate_status_not_applicable_only(self):
        self.set_user_context()
        self.assertEqual(self._task_with([self.S.NOT_APPLICABLE]).determine_aggregate_status(), self.St.NOT_APPLICABLE)

    # ---- Layer 1: with_aggregate_status() (SQL) ----
    def test_with_aggregate_status_no_outcomes_is_not_validated(self):
        self.set_user_context()
        t = self._task_with([])
        row = ValidationTask.objects.filter(id=t.id).with_aggregate_status().get()
        self.assertEqual(row.aggregate_status, self.St.NOT_VALIDATED)

    def test_with_aggregate_status_executed_is_valid(self):
        self.set_user_context()
        t = self._task_with([self.S.EXECUTED])
        row = ValidationTask.objects.filter(id=t.id).with_aggregate_status().get()
        self.assertEqual(row.aggregate_status, self.St.VALID)

    def test_with_aggregate_status_error_is_invalid(self):
        self.set_user_context()
        t = self._task_with([self.S.PASSED, self.S.ERROR])
        row = ValidationTask.objects.filter(id=t.id).with_aggregate_status().get()
        self.assertEqual(row.aggregate_status, self.St.INVALID)

    # ---- Layer 2: the *_calculated properties (the UI path) ----
    def test_schema_calculated_skipped_is_not_validated(self):
        self.assertEqual(self._model_with_task(self.T.SCHEMA, []).status_schema_calculated, self.St.NOT_VALIDATED)

    def test_ia_calculated_skipped_is_not_validated(self):
        self.assertEqual(self._model_with_task(self.T.NORMATIVE_IA, []).status_ia_calculated, self.St.NOT_VALIDATED)

    def test_ip_calculated_skipped_is_not_validated(self):
        self.assertEqual(self._model_with_task(self.T.NORMATIVE_IP, []).status_ip_calculated, self.St.NOT_VALIDATED)

    def test_schema_calculated_passed_is_valid(self):
        self.assertEqual(self._model_with_task(self.T.SCHEMA, [self.S.PASSED]).status_schema_calculated, self.St.VALID)

    def test_schema_calculated_error_is_invalid(self):
        self.assertEqual(self._model_with_task(self.T.SCHEMA, [self.S.PASSED, self.S.ERROR]).status_schema_calculated, self.St.INVALID)

    def test_calculated_missing_task_type_is_not_validated(self):
        # no SCHEMA task at all -> dict-miss default
        self.assertEqual(self._model_with_task(self.T.NORMATIVE_IA, [self.S.PASSED]).status_schema_calculated, self.St.NOT_VALIDATED)

class SplitLanguageTestCase(TestCase):

    def test_split_language_recognizes_language_markers(self):

        from apps.ifc_validation_models.languages import split_language

        test_cases = [
            ('Revit 26.4.0.32 (ENU)', 'Revit 26.4.0.32', 'en'),
            ('Revit 26.4.0.32 (ENG)', 'Revit 26.4.0.32', 'en'),
            ('Revit 27.0.0.0 (JPN)', 'Revit 27.0.0.0', 'ja'),
            ('AutodeskRevit2024(ENU)', 'AutodeskRevit2024', 'en'),
            ('Autodesk Revit 2022 (DEU)', 'Autodesk Revit 2022', 'de'),
            ('Autodesk Revit 2022 (FRA)', 'Autodesk Revit 2022', 'fr'),
            ('Autodesk Revit 2025 (CHS)', 'Autodesk Revit 2025', 'zh-hans'),
            ('Autodesk Civil 3D 2024 - English', 'Autodesk Civil 3D 2024', 'en'),
            ('Autodesk Civil 3D 2022 - Deutsch (German)', 'Autodesk Civil 3D 2022', 'de'),
            ('Autodesk Civil 3D 2020 - 日本語 (Japanese)', 'Autodesk Civil 3D 2020', 'ja'),
            ('SEMA Holzbausoftware 24.4.0.27 (de)', 'SEMA Holzbausoftware 24.4.0.27', 'de'),
            ('SEMA Holzbausoftware 24.4.0.27(de)', 'SEMA Holzbausoftware 24.4.0.27', 'de'),
            ('RhinoIFC (ENU)', 'RhinoIFC', 'en'),
            ('Revit(JPN)', 'Revit', 'ja'),
            ('Autodesk Civil 3D 2024 - English UK', 'Autodesk Civil 3D 2024', 'en'),
            ('Civil 3D 2023 - Português - Brasil (Brazilian Portuguese)', 'Civil 3D 2023', 'pt'),
            # non-breaking spaces and en-dash are normalized before matching
            ('Autodesk\xa0Civil\xa03D\xa02019 - Français (French)', 'Autodesk Civil 3D 2019', 'fr'),
            ('Autodesk Civil 3D 2019 – Français (French)', 'Autodesk Civil 3D 2019', 'fr'),
            # BCP 47 locale tags as used by the official buildingSMART translations
            ('Tool 2024 (de-DE)', 'Tool 2024', 'de'),
            ('Tool 2024 (zh-CN)', 'Tool 2024', 'zh-hans'),
            ('Tool 2024 (pt-BR)', 'Tool 2024', 'pt'),
            ('Tool 2024 [ja-JP]', 'Tool 2024', 'ja'),
            # language names taken from the buildingSMART translations repo
            ('Civil 3D 2024 - Swedish', 'Civil 3D 2024', 'sv'),
            ('Tool 2024 (Turkish)', 'Tool 2024', 'tr'),
            # lowercase ISO 639-2/639-3 codes, single or bibliographic/terminology pair
            ('Tool 2024 (fra)', 'Tool 2024', 'fr'),
            ('Tool 2024 (fra/fre)', 'Tool 2024', 'fr'),
            ('Tool 2024 (ger)', 'Tool 2024', 'de'),
            ('Tool 2024 (zho)', 'Tool 2024', 'zh'),
            # Autodesk LCID as a standalone token in the middle of the name
            ('Autodesk Revit 2025.1 (JPN) - J tool for Revit IFC2X3 2025', 'Autodesk Revit 2025.1 - J tool for Revit IFC2X3 2025', 'ja'),
            ('Autodesk Revit 2025.1 (ENU) - J tool for Revit IFC2X3 2025', 'Autodesk Revit 2025.1 - J tool for Revit IFC2X3 2025', 'en'),
            ('Revit 26.4.0.32 (ENU) 64-bit', 'Revit 26.4.0.32 64-bit', 'en'),
        ]

        for name, expected_canonical, expected_code in test_cases:
            with self.subTest(name=name):
                self.assertEqual(split_language(name), (expected_canonical, expected_code))

    def test_split_language_leaves_other_names_untouched(self):

        from apps.ifc_validation_models.languages import split_language

        # parenthesised tokens, dashes and codes that are NOT language packages
        test_cases = [
            'Quadri<26.0>',
            'VectorworksArchitect2013(Build167540)byNemetschekVectorworks,Inc.',
            'ACCA - usBIM',
            'usBIM - ACCA software',
            'ggRhinoIFC - Grasshopper3d Plug-in by Geometry Gym Pty Ltd',
            'Edificius - ACCA software S.p.A. - All Rights Reserved',
            'BIM Tool (IT)',          # uppercase 2-letter codes are ambiguous
            'Allplan (DE)',
            'SEMA (de) Holzbausoftware 24.4',   # ISO code in the middle stays end-anchored only
            'Tool (BETA) - plugin',
            'Revit 2025 (ENU)64-bit',           # no whitespace after the token
            'Tool 2024 (dev)',                  # three lowercase letters that are not a language code
            'Tool 2024 (pro)',
            'Tool (fra) Suite',                 # lowercase ISO codes are end-only
            'English',                # bare language name, no product name left
            '(ENU)',
            'IfcOpenShell-0.7.11-d51fa2c5f',
            'Civil Designer 9.1',
            '路桥隧数维设计软件',
            'ArCADia (wersja edukacyjna)',   # edition, not a language
            'Tool (BETA)',
            'Tool (demoversion)',
            'Tool (cadexchanger.com)',
            'Tool (t)',
            'IFC (text editor)',
            'Deutsch (German)',              # bare language name, no product name left
        ]

        for name in test_cases:
            with self.subTest(name=name):
                self.assertEqual(split_language(name), (name, None))

    def test_split_language_handles_empty_values(self):

        from apps.ifc_validation_models.languages import split_language

        self.assertEqual(split_language(None), (None, None))
        self.assertEqual(split_language(''), ('', None))

    def test_authoring_tool_stores_language_fields(self):

        ValidationModelsTestCase.set_user_context()

        company = Company.objects.create(name='Autodesk')
        tool = AuthoringTool.objects.create(
            company=company,
            name='Revit 26.4.0.32 (ENU)',
            version='26.4.0.32',
            canonical_name='Revit 26.4.0.32',
            language_code='en'
        )

        tool2 = AuthoringTool.objects.get(id=tool.id)
        self.assertEqual(tool2.canonical_name, 'Revit 26.4.0.32')
        self.assertEqual(tool2.language_code, 'en')

    def test_backfill_authoring_tools_derives_language_fields(self):

        from apps.ifc_validation_models.languages import backfill_authoring_tools

        ValidationModelsTestCase.set_user_context()

        company = Company.objects.create(name='Autodesk')
        marked = AuthoringTool.objects.create(company=company, name='Revit 26.4.0.32 (ESP)', version='26.4.0.32')
        plain = AuthoringTool.objects.create(company=company, name='Civil Designer 9.1', version='9.1')
        stale = AuthoringTool.objects.create(company=company, name='Revit 26.4.0.32 (ENU)', version='26.4.0.32')
        # simulate a row written before the allowlist knew this marker (bypasses save())
        AuthoringTool.objects.filter(pk=stale.pk).update(canonical_name=stale.name, language_code=None)

        # marked and plain were derived on save() already; only stale changes
        self.assertEqual(backfill_authoring_tools(AuthoringTool), 1)

        marked.refresh_from_db(); plain.refresh_from_db(); stale.refresh_from_db()
        self.assertEqual((marked.canonical_name, marked.language_code), ('Revit 26.4.0.32', 'es'))
        self.assertEqual((plain.canonical_name, plain.language_code), ('Civil Designer 9.1', None))
        self.assertEqual((stale.canonical_name, stale.language_code), ('Revit 26.4.0.32', 'en'))

        # idempotent: a second run changes nothing
        self.assertEqual(backfill_authoring_tools(AuthoringTool), 0)

    def test_authoring_tool_derives_language_fields_on_save(self):

        ValidationModelsTestCase.set_user_context()

        company = Company.objects.create(name='Autodesk')
        tool = AuthoringTool.objects.create(company=company, name='Revit 26.4.0.32 (ENU)', version='26.4.0.32')
        tool.refresh_from_db()
        self.assertEqual((tool.canonical_name, tool.language_code), ('Revit 26.4.0.32', 'en'))

        # renaming re-derives; an explicitly passed value never wins over the name
        tool.name = 'Revit 26.4.0.32'
        tool.canonical_name = 'something else'
        tool.save()
        tool.refresh_from_db()
        self.assertEqual((tool.canonical_name, tool.language_code), ('Revit 26.4.0.32', None))
