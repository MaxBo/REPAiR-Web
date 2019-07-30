SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_prod

GOTO REORDER
GOTO MERGE

python manage.py dump_object -k changes.solutioninstrategy --query "{\"solution__id\": 89}"  > repair\graph_fixtures\graph_solutioninstrategy.json
python manage.py dump_object -k asmfa.fractionflow --query "{\"keyflow__id\": 32}"  > repair\graph_fixtures\graph_fractionflow.json
python manage.py dump_object -k changes.solution --query "{\"id\": 89}"  > repair\graph_fixtures\graph_solutions.json
python manage.py dump_object -k changes.solutioninstrategy --query "{\"solution__id\": 89}"  > repair\graph_fixtures\graph_solutioninstrategy.json
python manage.py dump_object -k changes.actorinsolutionpart --query "{\"solutionpart__solution__id\": 89}"  > repair\graph_fixtures\graph_actorinsolutionpart.json
python manage.py dump_object -k changes.affectedflow --query "{\"solution_part__solution__id\": 89}"  > repair\graph_fixtures\graph_affectedflow.json

:MERGE
python manage.py merge_fixtures^
 repair\graph_fixtures\graph_solutions.json^
 repair\graph_fixtures\graph_solutioninstrategy.json^
 repair\graph_fixtures\graph_actorinsolutionpart.json^
 repair\graph_fixtures\graph_affectedflow.json^
 repair\graph_fixtures\graph_fractionflow.json^
 repair\graph_fixtures\graph_solutioninstrategy.json^
 > repair\graph_fixtures\graph_data_unordered.json


:REORDER

python manage.py reorder_fixtures repair\graph_fixtures\graph_data_unordered.json ^
 auth.group auth.user login.profile login.casestudy login.userincasestudy ^
 publications_bootstrap.type publications_bootstrap.publication ^
 publications.publicationincasestudy ^
 asmfa.keyflow asmfa.keyflowincasestudy asmfa.process ^
 asmfa.composition asmfa.product asmfa.waste asmfa.material asmfa.productfraction^
 studyarea.stakeholdercategory studyarea.stakeholder ^
 asmfa.reason ^
 asmfa.activitygroup asmfa.activity asmfa.actor ^
 asmfa.group2group asmfa.activity2activity asmfa.actor2actor ^
 asmfa.groupstock asmfa.activitystock asmfa.actorstock ^
 asmfa.fractionflow ^
 changes.solutioncategory changes.solution ^
 changes.solutionpart ^
 changes.implementationquestion ^
 changes.strategy changes.solutioninstrategy ^
 changes.implementationquantity ^
 changes.affectedflow ^
 studyarea.adminlevels studyarea.area ^
  > repair\graph_fixtures\graph_data.json
GOTO END

python manage.py dump_object --natural-foreign auth.group * --no-follow > repair\graph_fixtures\graph_groups.json
python manage.py dump_object asmfa.reason * > repair\graph_fixtures\graph_reason.json
python manage.py dump_object asmfa.material * > repair\graph_fixtures\graph_materials.json
python manage.py dump_object asmfa.waste * > repair\graph_fixtures\graph_wastes.json
python manage.py dump_object asmfa.product * > repair\graph_fixtures\graph_products.json
python manage.py dump_object asmfa.productfraction * > repair\graph_fixtures\graph_fractions.json
python manage.py dump_object -k login.casestudy --query "{\"id\": 2}" > repair\graph_fixtures\graph_casestudy.json
python manage.py dump_object --no-follow -k asmfa.keyflow * > repair\graph_fixtures\graph_keyflow.json
python manage.py dump_object -k asmfa.keyflowincasestudy --query "{\"id\": 1}" > repair\graph_fixtures\graph_keyflow_ic.json
python manage.py dump_object -k changes.solution --query "{\"id\": 18}"  > repair\graph_fixtures\graph_solutions.json



python manage.py merge_fixtures^
 repair\graph_fixtures\graph_groups.json^
 repair\graph_fixtures\graph_reason.json^
 repair\graph_fixtures\graph_casestudy.json^
 repair\graph_fixtures\graph_keyflow.json^
 repair\graph_fixtures\graph_keyflow_ic.json^
 repair\graph_fixtures\graph_products.json^
 repair\graph_fixtures\graph_wastes.json^
 repair\graph_fixtures\graph_materials.json^
 repair\graph_fixtures\graph_fractions.json^
 repair\graph_fixtures\graph_solutions.json^
 > repair\graph_fixtures\graph_data_unordered.json

GOTO END
python manage.py reorder_fixtures repair\graph_fixtures\graph_data_unordered.json ^
 auth.group auth.user login.profile login.casestudy login.userincasestudy ^
 asmfa.keyflow asmfa.keyflowincasestudy ^
 asmfa.composition asmfa.product asmfa.waste asmfa.material asmfa.productfraction^
 studyarea.stakeholdercategory studyarea.stakeholder ^
 studyarea.layercategory studyarea.stakeholder ^
 changes.solutioncategory changes.solution ^
 changes.strategy changes.solutioninstrategy ^
 changes.solutioninistrategynote changes.solutioninstrategygeometry ^
 studyarea.adminlevels studyarea.area ^
 asmfa.reason ^
 asmfa.activitygroup asmfa.activity asmfa.actor ^
 asmfa.group2group asmfa.activity2activity asmfa.actor2actor ^
 asmfa.groupstock asmfa.activitystock asmfa.actorstock ^
 statusquo.areaofprotection ^
 statusquo.impactcategory ^
 statusquo.sustainabilityfield ^
 statusquo.targetspatialreference ^
 statusquo.targetvalues ^
  > repair\graph_fixtures\graph_data.json

:END