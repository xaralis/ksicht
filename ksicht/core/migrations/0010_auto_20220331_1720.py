# Generated by Django 2.2.15 on 2022-03-31 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20220313_1151'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradeapplication',
            name='participant_current_grade',
            field=models.CharField(choices=[('4', '4.'), ('3', '3.'), ('2', '2.'), ('1', '1.'), ('l', 'nižší')], max_length=10, null=True, verbose_name='Ročník'),
        ),
    ]
