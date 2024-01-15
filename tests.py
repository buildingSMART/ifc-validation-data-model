import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from apps.ifc_validation_models.models import IfcValidationRequest, IfcValidationTask, IfcGherkinTaskResult  # TODO: for now needs to be absolute!
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
            file='test.ifc'
        )

        request2 = IfcValidationRequest.objects.get(id=request.id)

        self.assertEqual(request2.status, IfcValidationRequest.Status.PENDING)

    @requires_django_user_context
    def test_created_request_has_created_fields(self):

        request = IfcValidationRequest.objects.create(
            file_name='test2.ifc',
            file='test2.ifc'
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
            file='test3.ifc'
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
            file='test4.ifc'
        )

        task = IfcValidationTask.objects.create(
            request=request
        )

        task2 = IfcValidationTask.objects.get(id=task.id)

        self.assertEqual(task2.status, IfcValidationTask.Status.PENDING)

    @requires_django_user_context
    def test_created_tasks_can_be_navigated(self):

        request = IfcValidationRequest.objects.create(file_name='test5.ifc', file='test5.ifc')
        task1 = IfcValidationTask.objects.create(request=request)
        task2 = IfcValidationTask.objects.create(request=request)
        task3 = IfcValidationTask.objects.create(request=request)

        request2 = IfcValidationRequest.objects.create(file_name='test6.ifc', file='test6.ifc')
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
    def test_created_gherkin_results_can_be_navigated(self):

        request = IfcValidationRequest.objects.create(file_name='test7.ifc', file='test7.ifc')
        task1 = IfcValidationTask.objects.create(request=request)
        task2 = IfcValidationTask.objects.create(request=request)
        gherkin_result1 = IfcGherkinTaskResult.objects.create(request=request, task=task1, feature="RUL001 - Rule Description")
        gherkin_result2 = IfcGherkinTaskResult.objects.create(request=request, task=task1, feature="RUL002 - Rule Description")
        gherkin_result3 = IfcGherkinTaskResult.objects.create(request=request, task=task1, feature="RUL003 - Rule Description")
        gherkin_result4 = IfcGherkinTaskResult.objects.create(request=request, task=task2, feature="RUL001 - Rule Description")

        all_results = IfcGherkinTaskResult.objects.all()
        task1_results = IfcGherkinTaskResult.objects.filter(request__id=request.id).filter(task__id=task1.id)
        task2_results = IfcGherkinTaskResult.objects.filter(request__id=request.id).filter(task__id=task2.id)

        self.assertEqual(all_results.count(), 4)
        self.assertEqual(task1_results.count(), 3)
        self.assertEqual(task2_results.count(), 1)
        self.assertEqual(gherkin_result1.request.id, request.id)
        self.assertEqual(gherkin_result1.task.id, task1.id)
        self.assertEqual(gherkin_result1.id, task1_results[0].id)
        self.assertEqual(gherkin_result2.request.id, request.id)
        self.assertEqual(gherkin_result2.task.id, task1.id)
        self.assertEqual(gherkin_result2.id, task1_results[1].id)
        self.assertEqual(gherkin_result3.request.id, request.id)
        self.assertEqual(gherkin_result3.task.id, task1.id)
        self.assertEqual(gherkin_result3.id, task1_results[2].id)
        self.assertEqual(gherkin_result4.request.id, request.id)
        self.assertEqual(gherkin_result4.task.id, task2.id)
        self.assertEqual(gherkin_result4.id, task2_results[0].id)
