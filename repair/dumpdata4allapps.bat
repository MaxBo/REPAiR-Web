SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_pg
python manage.py dumpdata auth.group auth.user auth.user_groups --indent 2 --output "%~dp0apps\login\fixtures\auth.json"
python manage.py dumpdata login --indent 2 --output "%~dp0apps\login\fixtures\sandbox.json"
python manage.py dumpdata asmfa --indent 2 --output "%~dp0apps\asmfa\fixtures\sandbox.json"
python manage.py dumpdata studyarea --indent 2 --output "%~dp0apps\studyarea\fixtures\sandbox.json"
python manage.py dumpdata changes --indent 2 --output "%~dp0apps\changes\fixtures\sandbox.json"
python manage.py dumpdata reversions --indent 2 --output "%~dp0apps\reversions\fixtures\sandbox.json"
