import datetime
from time import sleep

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from apps.ifc_validation_models.models import IfcValidationRequest, IfcValidationTask  # TODO: for now needs to be absolute!
from apps.ifc_validation_models.models import IfcCompany, IfcAuthoringTool, IfcModel
from apps.ifc_validation_models.decorators import requires_django_user_context


class IfcValidationAppTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        """
        Creates a SYSTEM user in the (in-memory) database.
        Runs once for the whole test case.
        """

        user = User.objects.create(id=1, username='SYSTEM', is_active=True)
        user.save()

    @requires_django_user_context
    def test_created_request_has_status_pending(self):

        request = IfcValidationRequest.objects.create(
            file_name='test.ifc',
            file='test.ifc', 
            size=1024
        )

        request2 = IfcValidationRequest.objects.get(id=request.id)

        self.assertEqual(request2.status, IfcValidationRequest.Status.PENDING)

    @requires_django_user_context
    def test_created_request_has_created_fields(self):

        request = IfcValidationRequest.objects.create(
            file_name='test2.ifc',
            file='test2.ifc', 
            size=1024
        )

        request2 = IfcValidationRequest.objects.get(id=request.id)

        self.assertEqual(request2.created.date(), datetime.date.today())
        self.assertEqual(request2.created_by.username, 'SYSTEM')
        self.assertEqual(request2.created_by.id, 1)
        self.assertTrue(request2.updated is None)
        self.assertTrue(request2.updated_by is None)

    @requires_django_user_context
    def test_updated_request_has_updated_fields(self):

        request = IfcValidationRequest.objects.create(
            file_name='test3.ifc',
            file='test3.ifc',
            size=1024
        )

        request2 = IfcValidationRequest.objects.get(id=request.id)
        request2.save()  # simulate update

        self.assertEqual(request2.created.date(), datetime.date.today())
        self.assertEqual(request2.created_by.username, 'SYSTEM')
        self.assertEqual(request2.created_by.id, 1)
        self.assertEqual(request2.updated.date(), datetime.date.today())
        self.assertEqual(request2.updated_by.username, 'SYSTEM')
        self.assertEqual(request2.updated_by.id, 1)

    @requires_django_user_context
    def test_created_task_has_status_pending(self):

        request = IfcValidationRequest.objects.create(
            file_name='test4.ifc',
            file='test4.ifc',
            size=1024
        )

        task = IfcValidationTask.objects.create(
            request=request
        )

        task2 = IfcValidationTask.objects.get(id=task.id)

        self.assertEqual(task2.status, IfcValidationTask.Status.PENDING)

    @requires_django_user_context
    def test_created_tasks_can_be_navigated(self):

        request = IfcValidationRequest.objects.create(file_name='test5.ifc', file='test5.ifc', size=1024)
        task1 = IfcValidationTask.objects.create(request=request)
        task2 = IfcValidationTask.objects.create(request=request)
        task3 = IfcValidationTask.objects.create(request=request)

        request2 = IfcValidationRequest.objects.create(file_name='test6.ifc', file='test6.ifc', size=1024)
        IfcValidationTask.objects.create(request=request2)
        IfcValidationTask.objects.create(request=request2)

        all_tasks = IfcValidationTask.objects.all()
        tasks = IfcValidationTask.objects.filter(request__id=request.id)

        self.assertEqual(all_tasks.count(), 5)
        self.assertEqual(tasks.count(), 3)
        self.assertEqual(task1.id, tasks[0].id)
        self.assertEqual(task2.id, tasks[1].id)
        self.assertEqual(task3.id, tasks[2].id)

    @requires_django_user_context
    def test_newly_created_tool_and_model_can_be_navigated(self):

        user = User.objects.get(id=1)
        company = IfcCompany.objects.create(name='Acme Inc.')
        tool = IfcAuthoringTool.objects.create(name='Tool XYZ', version='1.0-alpha', company=company)
        model = IfcModel.objects.create(file_name='test_123.ifc', size=2048, produced_by=tool, uploaded_by=user)
        model2 = IfcModel.objects.create(file_name='test_xyz.ifc', size=4096, produced_by=tool, uploaded_by=user)

        all_tools = IfcAuthoringTool.objects.all()

        self.assertEqual(all_tools.count(), 1)
        self.assertEqual(all_tools[0].id, tool.id)
        self.assertEqual(tool.company.name, company.name)
        self.assertEqual(all_tools.first().company.name, company.name)
        self.assertEqual(model.produced_by.company.name, company.name)
        self.assertEqual(model.uploaded_by.username, user.username)
        self.assertEqual(user.models.count(), 2)
        self.assertEqual(user.models.all()[1].file_name, model2.file_name)

    @requires_django_user_context
    def test_find_tool_by_full_name_should_succeed(self):

        company1 = IfcCompany.objects.create(name='Acme Inc.')
        tool1 = IfcAuthoringTool.objects.create(name='Tool ABC', version='1.0', company=company1)
        tool2 = IfcAuthoringTool.objects.create(name='Tool ABC', version='2.0-alpha', company=company1)

        company2 = IfcCompany.objects.create(name='PyCAD Limited')
        tool3 = IfcAuthoringTool.objects.create(name='App', version=None, company=company2)
        tool4 = IfcAuthoringTool.objects.create(name='App', version='2024', company=company2)

        name_to_find = 'Acme Inc. Tool ABC - 1.0'
        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, IfcAuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

        name_to_find = 'Acme Inc. Tool ABC 1.0'
        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, IfcAuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

        name_to_find = 'PyCAD Limited'
        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNone(found_tool)

        name_to_find = 'PyCAD Limited App'
        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, IfcAuthoringTool)
        self.assertEqual(found_tool.name, tool3.name)

        name_to_find = 'PyCAD Limited App 2024'
        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, IfcAuthoringTool)
        self.assertEqual(found_tool.name, tool4.name)

        name_to_find = 'PyCAD Limited App 2020'
        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNone(found_tool)

    @requires_django_user_context
    def test_find_tool_by_full_name_should_succeed2(self):

        tool1 = IfcAuthoringTool.objects.create(name='Test Application', version='0.10')        

        name_to_find = 'Test Application 0.10'

        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, IfcAuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

        tool2 = IfcAuthoringTool.objects.create(name='Test Application', version='2023-01')        

        name_to_find = 'Test Application - 2023-01'

        found_tool = IfcAuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, IfcAuthoringTool)
        self.assertEqual(found_tool.name, tool2.name)

    @requires_django_user_context
    def test_model_can_navigate_back_to_request(self):
        
        request = IfcValidationRequest.objects.create(file_name='test.ifc', file='test.ifc', size=1024)
        
        model, _ =  IfcModel.objects.get_or_create(
            file_name = request.file_name,
            file = request.file,
            size = 0,
            uploaded_by = request.created_by
        )
        request.model = model
        request.save()

        request2 = IfcValidationRequest.objects.get(id=request.id)
        self.assertIsNotNone(request2.model)
        self.assertEqual(request.id, model.request.id)
        self.assertEqual(request2.id, model.request.id)

