# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-29 16:43
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import osf.models.base


DATE_FIELDS = ['startMonth', 'startYear', 'endMonth', 'endYear']


def populate_new_models(state, schema):
    OSFUser = state.get_model('osf', 'osfuser')
    Education = state.get_model('osf', 'education')
    Employment = state.get_model('osf', 'employment')

    users_with_education = OSFUser.objects.exclude(schools=[])
    set_model_content(Education, users_with_education, 'schools')

    users_with_employment = OSFUser.objects.exclude(jobs=[])
    set_model_content(Employment, users_with_employment, 'jobs')


def parse_model_datetime(month, year):
    month = format(month, '02')
    year = format(year, '02')
    try:
        parsed = datetime.strptime('{} {}'.format(month, year), '%m %Y')
    except ValueError:
        parsed = datetime.strptime('{} {}'.format(month, year), '%m %y')
    except ValueError:
        parsed = None
    return parsed


def set_model_content(model, queryset, original_attribute):
    for user in queryset:
        original_entries = getattr(user, original_attribute)
        for entry in original_entries:
            institution = entry.get('institution')
            if institution:
                new_object = model(
                    user=user,
                    institution=institution
                )
                for key, value in entry.items():
                    if key != 'institution' and key not in DATE_FIELDS:
                        setattr(new_object, key, value)

                start_year = entry.get('startYear', None)
                start_month = entry['startMonth'] if start_year else None
                if start_year and start_month:
                    new_object.start_date = parse_model_datetime(start_month, start_year)

                end_year = entry.get('endYear', None)
                end_month = entry['endMonth'] if end_year else None
                if end_year and end_month:
                    new_object.end_date = parse_model_datetime(end_month, end_year)

                new_object.save()

def reset_field_content(model, queryset, original_attribute):
    for entry in queryset:
        user = entry.user
        start_date = entry.start_date
        end_date = entry.end_date
        attributes = {
            'institution': entry.institution,
            'startYear': start_date.year if start_date else None,
            'startMonth': start_date.month if start_date else None,
            'endYear': end_date.month if end_date else None,
            'endMonth': end_date.month if end_date else None,
            'department': entry.department,
            'ongoing': entry.ongoing,
        }
        if original_attribute == 'schools':
            attributes['degree'] = entry.degree
        elif original_attribute == 'jobs':
            attributes['title'] = entry.title

        user_entries = getattr(user, original_attribute, [])
        user_entries.append(attributes)
        setattr(user, original_attribute, user_entries)
        user.save()

def put_jobs_and_schools_back(state, schema):
    Education = state.get_model('osf', 'education')
    Employment = state.get_model('osf', 'employment')

    education_queryset = Education.objects.all()
    reset_field_content(Education, education_queryset, 'schools')

    employment_queryset = Employment.objects.all()
    reset_field_content(Employment, employment_queryset, 'jobs')


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0181_osfuser_contacted_deactivation'),
    ]

    operations = [
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('_id', models.CharField(db_index=True, default=osf.models.base.generate_object_id, max_length=24, unique=True)),
                ('institution', models.CharField(max_length=650)),
                ('department', models.CharField(blank=True, max_length=650, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('ongoing', models.BooleanField(default=False)),
                ('degree', models.CharField(blank=True, max_length=650, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Employment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('_id', models.CharField(db_index=True, default=osf.models.base.generate_object_id, max_length=24, unique=True)),
                ('institution', models.CharField(max_length=650)),
                ('department', models.CharField(blank=True, max_length=650, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('ongoing', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=650, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employment', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterOrderWithRespectTo(
            name='employment',
            order_with_respect_to='user',
        ),
        migrations.AlterOrderWithRespectTo(
            name='education',
            order_with_respect_to='user',
        ),
        migrations.RunPython(populate_new_models, put_jobs_and_schools_back),
    ]