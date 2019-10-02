SET DJANGO_SETTINGS_MODULE=%DJANGO_SITENAME%.settings_prod

REM GOTO REORDER
REM GOTO MERGE
REM GOTO MERGE
REM GOTO END
python manage.py dump_object -k studyarea.stakeholder --query "{\"stakeholder_category__casestudy_id\": 7}"  > repair\graph_fixtures\graph_stakeholders.json

python manage.py dump_object -k changes.solutioninstrategy --query "{\"solution__id\": 89}"  > repair\graph_fixtures\graph_solutioninstrategy.json
python manage.py dump_object -k asmfa.fractionflow --query "{\"keyflow__id\": 32}"  > repair\graph_fixtures\graph_fractionflow.json
python manage.py dump_object -k asmfa.actor --query "{\"activity__activitygroup__keyflow__id\": 32}"  > repair\graph_fixtures\graph_actors.json
python manage.py dump_object -k changes.solution --query "{\"id\": 89}"  > repair\graph_fixtures\graph_solutions.json
python manage.py dump_object -k changes.solutioninstrategy --query "{\"solution__id\": 89}"  > repair\graph_fixtures\graph_solutioninstrategy.json
python manage.py dump_object -k changes.affectedflow --query "{\"solution_part__solution__id\": 89}"  > repair\graph_fixtures\graph_affectedflow.json

:MERGE
python manage.py merge_fixtures^
 repair\graph_fixtures\graph_stakeholders.json^
 repair\graph_fixtures\graph_solutions.json^
 repair\graph_fixtures\graph_solutioninstrategy.json^
 repair\graph_fixtures\graph_actors.json^
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
  > repair\graph_fixtures\peelpioneer_data.json
GOTO END


GOTO END


:END
