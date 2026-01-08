import os
from django.db import models

from django.db import models
from django.contrib.auth.models import User

import os


def candidate_profile_path(instance, filename):
    safe_name = instance.name.replace(" ", "_") if instance.name else "candidate"
    return f"candidate/{safe_name}-{instance.id}/profile/profile{os.path.splitext(filename)[1]}"


def candidate_document_path(instance, filename):
    candidate = instance.candidate
    safe_name = candidate.name.replace(" ", "_")
    doc_type = instance.document_type.document_type.replace(" ", "_").upper()
    ext = os.path.splitext(filename)[1]

    return f"candidate/{safe_name}-{candidate.id}/documents/{safe_name}-{candidate.id}_{doc_type}{ext}"


