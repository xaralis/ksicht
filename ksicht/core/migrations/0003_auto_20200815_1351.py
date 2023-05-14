# Generated by Django 2.2.10 on 2020-08-15 13:51

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_auto_20200628_0546"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_public",
            field=models.BooleanField(
                default=True,
                help_text="Neveřejné akce se zobrazí jen níže uvedeným osobám.",
                verbose_name="Veřejná akce",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="publish_occupancy",
            field=models.BooleanField(
                default=True,
                help_text="Pokud je zaškrtnuto, u akce se zobrazí kapacita i aktuální obsazenost.",
                verbose_name="Zveřejnit počet účastníků",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="visible_to",
            field=models.ManyToManyField(
                help_text="Využijte pro neveřejné akce. Pokud je akce neveřejná, bude se zobrazovat jen zde vybraným uživatelům. U veřejných akcí se nezohledňuje.",
                related_name="private_events",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Viditelné pro tyto uživatele",
                blank=True,
            ),
        ),
    ]
