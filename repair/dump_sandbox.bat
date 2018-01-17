SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_prod
python manage.py dump_object -k login.casestudy --query "{\"id\": 7}" > repair\fixtures\sandbox_casestudy.json
python manage.py dump_object -k asmfa.keyflowincasestudy --query "{\"casestudy__id\": 7}" > repair\fixtures\sandbox_keyflow.json
python manage.py dump_object -k asmfa.productfraction --query "{\"product__keyflow__casestudy__id\": 7}"  > repair\fixtures\sandbox_products.json
python manage.py dump_object -k studyarea.area --query "{\"casestudy__id\": 7}"  > repair\fixtures\sandbox_areas.json
python manage.py dump_object -k changes.solutioninimplementation --query "{\"implementation__user__casestudy__id\": 5}"  > repair\fixtures\sandbox_solutions.json
python manage.py dump_object -k changes.solutionratiooneunit --query "{\"solution__user__casestudy__id\": 5}"  > repair\fixtures\sandbox_solutionsratio.json
python manage.py dump_object -k changes.strategy --query "{\"user__casestudy__id\": 5}"  > repair\fixtures\sandbox_strategy.json
python manage.py merge_fixtures^
 repair\fixtures\sandbox_casestudy.json^
 repair\fixtures\sandbox_areas.json^
 repair\fixtures\sandbox_keyflow.json^
 repair\fixtures\sandbox_products.json^
 repair\fixtures\sandbox_solutions.json^
 repair\fixtures\sandbox_solutionsratio.json^
 repair\fixtures\sandbox_strategy.json^
 > repair\fixtures\sandbox_data.json
