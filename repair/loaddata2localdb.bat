SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_staged

python manage.py migrate --run-syncdb
python manage.py loaddata sandbox_data

goto skip_single_loading_of_fixtures_for_debugging
python manage.py loaddata sandbox_groups
python manage.py loaddata sandbox_casestudy
python manage.py loaddata sandbox_areas
python manage.py loaddata sandbox_keyflow
python manage.py loaddata sandbox_materials
python manage.py loaddata sandbox_products
python manage.py loaddata sandbox_wastes
python manage.py loaddata sandbox_fractions
python manage.py loaddata sandbox_solutions
python manage.py loaddata sandbox_solutionsratio
python manage.py loaddata sandbox_strategy
python manage.py loaddata sandbox_publications
python manage.py loaddata sandbox_areas
python manage.py loaddata sandbox_actor
python manage.py loaddata sandbox_stakeholders
:skip_single_loading_of_fixtures_for_debugging