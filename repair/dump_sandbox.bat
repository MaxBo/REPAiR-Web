SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_dev_local_pg
python manage.py dump_object --natural-foreign auth.group * --no-follow > repair\fixtures\sandbox_groups.json
python manage.py dump_object asmfa.reason * > repair\fixtures\sandbox_reason.json
python manage.py dump_object asmfa.waste * > repair\fixtures\sandbox_wastes.json
python manage.py dump_object asmfa.product * > repair\fixtures\sandbox_products.json
python manage.py dump_object statusquo.areaofprotection * > repair\fixtures\sandbox_areasofprotection.json
python manage.py dump_object statusquo.impactcategory * > repair\fixtures\sandbox_impactcategories.json
python manage.py dump_object statusquo.sustainabilityfield * > repair\fixtures\sandbox_sustainabilityfields.json
python manage.py dump_object statusquo.targetspatialreference * > repair\fixtures\sandbox_targetspatialreferences.json
python manage.py dump_object statusquo.targetvalue * > repair\fixtures\sandbox_targetvalues.json
python manage.py dump_object --no-follow asmfa.material * > repair\fixtures\sandbox_materials.json
python manage.py dump_object --no-follow asmfa.productfraction * > repair\fixtures\sandbox_fractions.json
python manage.py dump_object -k login.casestudy --query "{\"id\": 7}" > repair\fixtures\sandbox_casestudy.json
python manage.py dump_object -k asmfa.actor --query "{\"activity__activitygroup__keyflow__casestudy__id\": 7}" > repair\fixtures\sandbox_actor.json
python manage.py dump_object -k asmfa.keyflowincasestudy --query "{\"casestudy__id\": 7}" > repair\fixtures\sandbox_keyflow.json
python manage.py dump_object -k changes.solutioninstrategy --query "{\"strategy__keyflow__casestudy__id\": 7}"  > repair\fixtures\sandbox_solutions.json
python manage.py dump_object -k changes.solutionratiooneunit --query "{\"solution__user__casestudy__id\": 7}"  > repair\fixtures\sandbox_solutionsratio.json
python manage.py dump_object -k changes.strategy --query "{\"keyflow__casestudy__id\": 7}"  > repair\fixtures\sandbox_strategy.json
python manage.py dump_object -k publications_bootstrap.publication * > repair\fixtures\sandbox_publications.json
python manage.py dump_object -k studyarea.area --query "{\"adminlevel__casestudy__id\": 7}"  > repair\fixtures\sandbox_areas.json
python manage.py dump_object -k studyarea.stakeholdercategory --query "{\"casestudy__id\": 7}"  > repair\fixtures\sandbox_stakeholders.json
python manage.py dump_object -k studyarea.layercategory --query "{\"casestudy__id\": 7}"  > repair\fixtures\sandbox_layers.json

python manage.py merge_fixtures^
 repair\fixtures\sandbox_groups.json^
 repair\fixtures\sandbox_reason.json^
 repair\fixtures\sandbox_casestudy.json^
 repair\fixtures\sandbox_areas.json^
 repair\fixtures\sandbox_keyflow.json^
 repair\fixtures\sandbox_products.json^
 repair\fixtures\sandbox_wastes.json^
 repair\fixtures\sandbox_keyflow_materials.json^
 repair\fixtures\sandbox_solutions.json^
 repair\fixtures\sandbox_solutionsratio.json^
 repair\fixtures\sandbox_strategy.json^
 repair\fixtures\sandbox_publications.json^
 repair\fixtures\sandbox_areas.json^
 repair\fixtures\sandbox_actor.json^
 repair\fixtures\sandbox_stakeholders.json^
 repair\fixtures\sandbox_layers.json^
 repair\fixtures\sandbox_areasofprotection.json^
 repair\fixtures\sandbox_impactcategories.json^
 repair\fixtures\sandbox_sustainabilityfields.json^
 repair\fixtures\sandbox_targetspatialreferences.json^
 repair\fixtures\sandbox_targetvalues.json^
 > repair\fixtures\sandbox_data_unordered.json

python manage.py reorder_fixtures repair\fixtures\sandbox_data_unordered.json ^
 auth.group auth.user login.profile login.casestudy login.userincasestudy ^
 asmfa.composition asmfa.product asmfa.waste asmfa.material ^
 studyarea.stakeholdercategory studyarea.stakeholder ^
 studyarea.layercategory studyarea.stakeholder ^
 changes.unit changes.solutioncategory changes.solution changes.solutionquantity changes.solutionratiooneunit ^
 changes.strategy changes.solutioninstrategy ^
 changes.solutioninistrategynote changes.solutioninstrategyquantity changes.solutioninstrategygeometry ^
 studyarea.adminlevels studyarea.area ^
 asmfa.reason ^
 asmfa.keyflow asmfa.keyflowincasestudy asmfa.product asmfa.material ^
 asmfa.activitygroup asmfa.activity asmfa.actor ^
 asmfa.group2group asmfa.activity2activity asmfa.actor2actor ^
 asmfa.groupstock asmfa.activitystock asmfa.actorstock ^
 statusquo.areaofprotection ^
 statusquo.impactcategory ^
 statusquo.sustainabilityfield ^
 statusquo.targetspatialreference ^
 statusquo.targetvalues ^
  > repair\fixtures\sandbox_data.json
