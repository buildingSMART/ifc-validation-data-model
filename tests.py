from django.test import TestCase
from django.contrib.auth.models import User

from apps.ifc_validation_models.models import ValidationRequest, ValidationTask  # TODO: for now needs to be absolute!
from apps.ifc_validation_models.models import Company, AuthoringTool, Model
from apps.ifc_validation_models.models import set_user_context

class ValidationModelsTestCase(TestCase):

    def set_user_context():
        user = User.objects.create(id=1, username='SYSTEM', is_active=True)
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
        self.assertEqual(all_tools.first().company.name, company.name)
        self.assertEqual(model.produced_by.company.name, company.name)
        self.assertEqual(model.uploaded_by.username, user.username)
        self.assertEqual(user.models.count(), 2)
        self.assertEqual(user.models.all()[1].file_name, model2.file_name)

    def test_find_tool_by_full_name_should_succeed(self):

        ValidationModelsTestCase.set_user_context()
        company1 = Company.objects.create(name='Acme Inc.')
        tool1 = AuthoringTool.objects.create(name='Tool ABC', version='1.0', company=company1)
        tool2 = AuthoringTool.objects.create(name='Tool ABC', version='2.0-alpha', company=company1)

        company2 = Company.objects.create(name='PyCAD Limited')
        tool3 = AuthoringTool.objects.create(name='App', version=None, company=company2)
        tool4 = AuthoringTool.objects.create(name='App', version='2024', company=company2)

        name_to_find = 'Acme Inc. - Tool ABC - 1.0'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

        name_to_find = 'Acme Inc. - Tool ABC 1.0'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

        name_to_find = 'PyCAD Limited'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNone(found_tool)

        name_to_find = 'PyCAD Limited App'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool3.name)

        name_to_find = 'PyCAD Limited - App 2024'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool4.name)

        name_to_find = 'PyCAD Limited App 2020'
        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNone(found_tool)

    def test_find_tool_by_full_name_should_succeed2(self):

        ValidationModelsTestCase.set_user_context()
        tool1 = AuthoringTool.objects.create(name='Test Application', version='0.10')        

        name_to_find = 'Test Application 0.10'

        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

        tool2 = AuthoringTool.objects.create(name='Test Application', version='2023-01')        

        name_to_find = 'Test Application - 2023-01'

        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool2.name)

    def test_find_tool_by_full_name_should_succeed3(self):

        ValidationModelsTestCase.set_user_context()
        tool1 = AuthoringTool.objects.create(name='IfcOpenShell-v0.7.0-6c9e130ca', version='v0.7.0-6c9e130ca')        

        name_to_find = 'IfcOpenShell-v0.7.0-6c9e130ca v0.7.0-6c9e130ca'

        found_tool = AuthoringTool.find_by_full_name(name_to_find)
        self.assertIsNotNone(found_tool)
        self.assertIsInstance(found_tool, AuthoringTool)
        self.assertEqual(found_tool.name, tool1.name)

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
            type=ValidationTask.Type.PARSE_INFO
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

