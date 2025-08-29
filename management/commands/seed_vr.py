from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.contrib.auth import get_user_model
from apps.ifc_validation_models.models import ValidationRequest, set_user_context

class Command(BaseCommand):
    help = "Seed a ValidationRequest with given timestamps."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="file_name of the VR")
        parser.add_argument("--created", required=True, help="ISO datetime (Z ok)")
        parser.add_argument("--started", required=True, help="ISO datetime (Z ok)")

    def handle(self, *args, **opts):
        user = get_user_model().objects.get(username="root")
        set_user_context(user)

        vr = ValidationRequest(file_name=opts["file"], file="dummy.ifc", size=1234)
        vr.save()

        created = parse_datetime(opts["created"])
        started = parse_datetime(opts["started"])
        ValidationRequest.objects.filter(id=vr.id).update(created=created, started=started)

        self.stdout.write(str(vr.id))
