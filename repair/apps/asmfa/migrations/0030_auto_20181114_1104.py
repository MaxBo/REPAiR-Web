# Generated by Django 2.0 on 2018-11-14 10:04

from django.db import migrations, models
import repair.apps.utils.protect_cascade


class Migration(migrations.Migration):

    dependencies = [
        ('asmfa', '0029_auto_20180503_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='activitygroup',
            field=models.ForeignKey(on_delete=repair.apps.utils.protect_cascade.PROTECT_CASCADE, to='asmfa.ActivityGroup'),
        ),
        migrations.AlterField(
            model_name='activitygroup',
            name='keyflow',
            field=models.ForeignKey(on_delete=repair.apps.utils.protect_cascade.PROTECT_CASCADE, to='asmfa.KeyflowInCasestudy'),
        ),
        migrations.AlterField(
            model_name='actor',
            name='activity',
            field=models.ForeignKey(on_delete=repair.apps.utils.protect_cascade.PROTECT_CASCADE, to='asmfa.Activity'),
        ),
    ]