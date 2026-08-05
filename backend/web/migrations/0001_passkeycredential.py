from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="PasskeyCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("credential_id", models.BinaryField(unique=True)),
                ("public_key", models.BinaryField()),
                ("user_handle", models.BinaryField(unique=True)),
                ("sign_count", models.PositiveBigIntegerField(default=0)),
                ("transports", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("disabled", models.BooleanField(default=False)),
            ],
        ),
    ]
