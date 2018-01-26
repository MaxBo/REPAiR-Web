SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_staged
python manage.py dump_object auth.group * --no-follow > repair\fixtures\sandbox_groups.json
python manage.py dump_object asmfa.reason * > repair\fixtures\sandbox_reason.json
python manage.py dump_object -k login.casestudy --query "{\"id\": 7}" > repair\fixtures\sandbox_casestudy.json
python manage.py dump_object -k asmfa.actor --query "{\"activity__activitygroup__keyflow__casestudy__id\": 7}" > repair\fixtures\sandbox_actor.json
python manage.py dump_object -k asmfa.keyflowincasestudy --query "{\"casestudy__id\": 7}" > repair\fixtures\sandbox_keyflow.json
python manage.py dump_object -k asmfa.productfraction --query "{\"product__keyflow__casestudy__id\": 7}"  > repair\fixtures\sandbox_products.json
python manage.py dump_object -k changes.solutioninimplementation --query "{\"implementation__user__casestudy__id\": 7}"  > repair\fixtures\sandbox_solutions.json
python manage.py dump_object -k changes.solutionratiooneunit --query "{\"solution__user__casestudy__id\": 7}"  > repair\fixtures\sandbox_solutionsratio.json
python manage.py dump_object -k changes.strategy --query "{\"user__casestudy__id\": 7}"  > repair\fixtures\sandbox_strategy.json
python manage.py dump_object -k publications_bootstrap.publication * > repair\fixtures\sandbox_publications.json
python manage.py dump_object -k studyarea.area --query "{\"adminlevel__casestudy__id\": 7}"  > repair\fixtures\sandbox_areas.json
python manage.py dump_object -k studyarea.stakeholdercategory --query "{\"casestudy__id\": 7}"  > repair\fixtures\sandbox_stakeholders.json

python manage.py merge_fixtures^
 repair\fixtures\sandbox_groups.json^
 repair\fixtures\sandbox_reason.json^
 repair\fixtures\sandbox_casestudy.json^
 repair\fixtures\sandbox_areas.json^
 repair\fixtures\sandbox_keyflow.json^
 repair\fixtures\sandbox_products.json^
 repair\fixtures\sandbox_solutions.json^
 repair\fixtures\sandbox_solutionsratio.json^
 repair\fixtures\sandbox_strategy.json^
 repair\fixtures\sandbox_publications.json^
 repair\fixtures\sandbox_areas.json^
 repair\fixtures\sandbox_actor.json^
 repair\fixtures\sandbox_stakeholders.json^
 > repair\fixtures\sandbox_data_unordered.json

python manage.py reorder_fixtures repair\fixtures\sandbox_data_unordered.json ^
 auth.group auth.user login.profile login.casestudy login.userincasestudy ^
 studyarea.stakeholdercategory studyarea.stakeholder ^
 changes.unit changes.solutioncategory changes.solution changes.solutionquantity changes.solutionratiooneunit ^
 changes.implementation changes.solutioninimplementation ^
 changes.solutioninimplementationnote changes.solutioninimplementationquantity changes.solutioninimplementationgeometry ^
 changes.strategy ^
 studyarea.adminlevels studyarea.area ^
 asmfa.reason ^
 asmfa.dataentry ^
 asmfa.keyflow asmfa.keyflowincasestudy asmfa.product asmfa.material asmfa.productfraction ^
 asmfa.activitygroup asmfa.activity asmfa.actor ^
 asmfa.group2group asmfa.activity2activity asmfa.actor2actor ^
 asmfa.groupstock asmfa.activitystock asmfa.actorstock ^
  > repair\fixtures\sandbox_data.json