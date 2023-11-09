# Generated by Django 4.1.7 on 2023-11-09 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_alter_option_unique_together"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="option",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="question",
            name="text",
            field=models.CharField(default="New Question", max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name="answeroption",
            unique_together={("value", "answer")},
        ),
    ]