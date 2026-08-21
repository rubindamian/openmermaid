import secrets
import uuid

from django.conf import settings
from django.db import models


def new_public_token() -> str:
    return secrets.token_urlsafe(24)


class Diagram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="diagrams",
    )
    title = models.CharField(max_length=255, default="Untitled")
    source_draft = models.TextField(blank=True, default="")
    source_published = models.TextField(blank=True, default="")
    public_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    png_published = models.BinaryField(null=True, blank=True)
    saved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"
