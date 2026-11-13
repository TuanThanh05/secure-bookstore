from django.db import models
from django.utils import timezone


class SecurityEvent(models.Model):
    event_type = models.CharField(max_length=40)
    severity = models.CharField(max_length=10, default="info")
    user_id = models.BigIntegerField(null=True, blank=True)
    username_attempted = models.CharField(max_length=150, null=True, blank=True)
    ip_address = models.CharField(max_length=45)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=10, null=True, blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    detail = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "core_securityevent"