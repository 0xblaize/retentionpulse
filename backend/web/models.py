from django.db import models


class PasskeyCredential(models.Model):
    credential_id = models.BinaryField(unique=True)
    public_key = models.BinaryField()
    user_handle = models.BinaryField(unique=True)
    sign_count = models.PositiveBigIntegerField(default=0)
    transports = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return self.user_handle.hex()
