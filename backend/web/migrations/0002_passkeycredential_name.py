from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web", "0001_passkeycredential"),
    ]

    operations = [
        migrations.AddField(
            model_name="passkeycredential",
            name="name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
