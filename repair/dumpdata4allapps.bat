SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_pg
python manage.py dumpdata auth.group auth.user auth.user_groups --indent 2 --output "%~dp0apps\login\fixtures\auth_fixture.json"
python manage.py dumpdata login --indent 2 --output "%~dp0apps\login\fixtures\user_fixture.json"
python manage.py dumpdata asmfa --indent 2 --output "%~dp0apps\asmfa\fixtures\activities_dummy_data.json"
python manage.py dumpdata studyarea --indent 2 --output "%~dp0apps\studyarea\fixtures\stakeholder_fixture.json"
python manage.py dumpdata changes --indent 2 --output "%~dp0apps\changes\fixtures\changes_fixture.json
"