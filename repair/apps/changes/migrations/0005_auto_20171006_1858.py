# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-06 16:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('changes', '0004_auto_20171006_1856'),
    ]

    operations = [
        migrations.CreateModel(
            name='Strategy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('casestudy_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='changes.CaseStudy')),
                ('implementations', models.ManyToManyField(to='changes.Implementation')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='changes.UserAP34')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='strategy',
            unique_together=set([('casestudy_id', 'user_id', 'name')]),
        ),
    ]
