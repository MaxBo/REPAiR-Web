SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings
python manage.py migrate --run-syncdb
python manage.py loaddata auth_fixture.json login_fixture.json activities_dummy_data.json stakeholder_fixture.json changes_fixture.json