# Generated by Django 4.1.7 on 2023-04-09 05:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_alter_option_position_alter_option_unique_together"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="option",
            unique_together=set(),
        ),
    ]
