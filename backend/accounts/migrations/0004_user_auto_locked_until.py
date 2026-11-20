from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_two_factor_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auto_locked_until",
            field=models.DateTimeField(blank=True, null=True, verbose_name="khóa tự động đến"),
        ),
    ]
