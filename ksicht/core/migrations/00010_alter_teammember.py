from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_participant_brochures_by_mail"),
    ]

    operations = [
        migrations.AddField(
            model_name="TeamMember",
            name="role",
            field=models.CharField(verbose_name="Role", max_length=150, blank=True),
        ),
        migrations.AddField(
            model_name="TeamMember",
            name="url_fb",
            field=models.URLField(verbose_name="Odkaz na Facebook", blank=True),
        ),
        migrations.AddField(
            model_name="TeamMember",
            name="url_ig",
            field=models.URLField(verbose_name="Odkaz na Instagramu", blank=True),
        ),
        migrations.AddField(
            model_name="TeamMember",
            name="url_other",
            field=models.URLField(verbose_name="Odkaz na vlastní web", blank=True),
        ),
    ]
