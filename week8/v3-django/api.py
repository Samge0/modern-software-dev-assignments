"""Notes CRUD API — Django + DRF (Version 3, non-JS-language requirement).

Single-file Django setup so the whole version lives in one module:
configures settings, defines the model/view/urls, and exposes `app` via
WSGI. Run: python manage-less.py runserver 8003  (or use the runner below).
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

settings = {
    "DEBUG": True,
    "SECRET_KEY": "week8-demo-not-for-production",
    "ALLOWED_HOSTS": ["*"],
    "INSTALLED_APPS": [
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "rest_framework",
    ],
    "DATABASES": {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "notes.db",
        }
    },
    "ROOT_URLCONF": __name__,
    "USE_TZ": True,
    "REST_FRAMEWORK": {
        "DEFAULT_PAGINATION_CLASS": None,
        "UNAUTHENTICATED_USER": None,
    },
}

import django  # noqa: E402
from django.conf import settings as dj_settings  # noqa: E402

if not dj_settings.configured:
    dj_settings.configure(**settings)
    django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()

# --- model & endpoints registered on Django's app registry ------------------
from django.db import models  # noqa: E402
from rest_framework import serializers, viewsets  # noqa: E402
from rest_framework.decorators import api_view  # noqa: E402
from rest_framework.response import Response  # noqa: E402
from django.urls import path  # noqa: E402


class Note(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "notes_app"


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at"]


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET", "POST"])
def notes_collection(request):
    if request.method == "GET":
        qs = Note.objects.all().order_by("-id")
        return Response(NoteSerializer(qs, many=True).data)
    ser = NoteSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    note = ser.save()
    return Response(NoteSerializer(note).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def note_item(request, note_id: int):
    try:
        note = Note.objects.get(pk=note_id)
    except Note.DoesNotExist:
        return Response({"error": "note not found"}, status=404)

    if request.method == "GET":
        return Response(NoteSerializer(note).data)
    if request.method == "PUT":
        ser = NoteSerializer(note, data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
    note.delete()
    return Response(status=204)


urlpatterns = [
    path("health", health),
    path("notes", notes_collection),
    path("notes/<int:note_id>", note_item),
]


def main() -> None:
    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, interactive=False, verbosity=0)
    # create tables for our app_label (no migrations shipped)
    from django.db import connection

    with connection.schema_editor() as editor:
        editor.create_model(Note)
    from django.core.servers.runserver import run

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8003
    print(f"Django notes API on http://127.0.0.1:{port}")
    run("127.0.0.1", port, get_wsgi_application())


if __name__ == "__main__":
    main()
