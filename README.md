# REPAiR-Web
[![CircleCI](https://circleci.com/gh/MaxBo/REPAiR-Web/tree/master.svg?style=shield&circle)](https://circleci.com/gh/MaxBo/REPAiR-Web/tree/master)
[![codecov](https://codecov.io/gh/MaxBo/REPAiR-Web/branch/master/graph/badge.svg)](https://codecov.io/gh/MaxBo/REPAiR-Web)

REPAiR Programmer’s Guide

#  Setting Up Django



* Pull project from [https://github.com/MaxBo/REPAiR-Web https://github.com/MaxBo/REPAiR-Web]
* ''Optional: Create and activate a python-environment''
* Register repair-package and Install dependencies with 

'''''pip install -r <nowiki>requirements-dev.tx</nowiki>t'''''

* Depending on your IDE you may have to set up the environment variable of the sitename manually (DJANGO_SITENAME=repair), e.g. in WingIDE under ''Project Properties &gt; Environment''
* Create a database based on used models with '''''python <nowiki>manage.py</nowiki> migrate'''''
* Start the server on localhost with '''''python <nowiki>manage.py</nowiki> runserver &lt;port-number&gt; '''''

    website is then accessible in browser via ''localhost:&lt;port-number&gt;''



# Package/Folder Structure



'''Packages'''

{| class="prettytable"
|-
|
package

|
module

|
description

|-
|
repair

|
-

|
this is our base package including all the custom modules for running the server and client

|-
|


|
settings

|
important file setting up the installed apps and the folder-structure (location of the template-directory, static files etc.)

|-
|


|
urls

|
maps the urls to functions called when accessing specific urls (relative to the base-url)

|-
|


|
wsgi

|
specification for communication between server and web application (definitions are done in settings-module)

|-
|
<nowiki>repair.ap</nowiki>ps

|
-

|
the web applications (aka subsites)

|-
|
<nowiki>repair.apps.st</nowiki>udy_area



|
-

|
example app (mapped in <nowiki>repair.ur</nowiki>ls to  ''&lt;base-url&gt;/study_area'')

|-
|


|
urls

|
maps the urls to functions (relative to ''&lt;base-url&gt;/study_area'')

|-
|


|
models

|
the data required by the app, contains essential fields and behaviors of the data (stored in database)

|-
|


|
serializers

|
definitions how to serialize the data (models) in order to communicate it between server and client

|-
|


|
views

|
definition of what to show client-side; render template on request and fill it with content (diagrams, texts etc.)

|-
|


|
tests

|
Unit-tests of this app (see 4.)

|-
|
<nowiki>repair.apps.study_area.mi</nowiki>grations

|
-

|
definitions of how to store the models inside the database

|}




'''Paths and files '''(packages not listed)

{| class="prettytable"
|-
|
path

|
description

|-
|
/repair/locale

|
localizations of texts (see 5.)

|-
|
/repair/templates

|
the templates for client-side rendering of pages (django-function get_template(‘’) is configured to point to this directory)

|-
|
/repair/templates<nowiki>/base.ht</nowiki>ml

|
basic template all other templates which render subsites should derive from; contains the basic structure of the site and the navigation-bar

|-
|
/repair/templates<nowiki>/index.ht</nowiki>ml

|
the welcome page

|-
|
/repair/templates/study_area<nowiki>/index.ht</nowiki>ml

|
the template used by the example app (see previous table)

|-
|
/repair/static

|
static files required client-side like Javascript-scripts,  images and fonts; 

accessible in code/html via constant variable '''''STATIC_URL'''''

|-
|
/repair/static/css

|
style-sheets for defining style of web-site when rendering templates client-side (ids, classes have to correspond to tags used in the templates)

|-
|
/repair/static/fonts

|
fonts included in templates

|-
|
/repair/static/img

|
images

|-
|
/repair/static/js

|
javascript libraries and scripts (see 3.)

|}




# Javascript Modularisation
* the modularization is achieved by using django-require (post-processor for optimizing with RequireJS)
* paths and variables for django-require are set up in <nowiki>repair.se</nowiki>ttings, require-path is set to '''''/repair/static/js/'''''
* organized as apps (analog to django-apps)
* currently one app for organizing javascript-code called <nowiki>app.js</nowiki> 
* <nowiki>app.js</nowiki> is loaded in template via ''{% require_module 'app' %}''
* <nowiki>app.js</nowiki> defines all required javascript-modules and maps them to custom names; will load them on demand
* <nowiki>app.js</nowiki> currently inits the main app for the study_area (/repair/static/js/app<nowiki>/main.js</nowiki>); this may change in the future as we need more specific apps for the different subsites/tasks
* <nowiki>main.js</nowiki> defines which modules it needs (will then be loaded directly, if not already done) and contains the functionality what to do on certain events in the DOM
# Continuous Development / Testing
* '''Workflow:'''

'''Don’t push directly into the master branch!'''

# Checkout to new branch.
# Write a test.
# Write new Code and label strings for translation.
# Commit and push to your branch.
# Create pull-request on Github.
# Wait for CircleCi to test the code.
## If build was successfull:
### Merge your branch into master.
## Else:
### Fix the error, restart at 4., …
# Server automatically pulls master branch.
# Website is updated and you can start at 1. again.

    Have a look at <nowiki>Workflow.pd</nowiki>f for further information.





* Automatic server updates via Webhook
** We use a Github-webhook to keep our website up-to-date. That means: Changes (push and pull requests) to the master-branch trigger a webhook-event, that is sent from github to ''[http://geodesignhub.h2020repair.bk.tudelft.nl/api/payload http://geodesignhub.h2020repair.bk.tudelft.nl/api/payload'']. This event calls a function that automatically pulls the current master branch, so that our website is always up-to-date with the remote master branch.



* Continuous Integration with CircleCi
** We use Continuous Integration to test the code before it is merged to our master branch. This helps to detect errors before our website is updated with new code. Every time someone pushes new commits to any branch of our remote repository, CircleCi creates a build environment and runs our tests on their servers. This takes about 1-2 minutes. You can review the current build status here: ''[https://circleci.com/gh/MaxBo https://circleci.com/gh/MaxBo'']. The github repository settings require a successful CircleCi-build in order to merge them to the master branch. This means: '''No one (except MaxBo) can directly push any commits to our master branch.''' If you want to commit something, create a new branch, commit and push to that branch and create a pull request. CircleCi automatically tests that branch and if all tests run successfully you can merge the new code from your branch to the master branch. For more information look at the Workflow section.



* Testing
** Django tests are directly written into the apps directory. For example: The tests for the study_area section are written into ''../repair/apps/study_area<nowiki>/tests.py</nowiki>''.
** Basic structure:



''from <nowiki>django.te</nowiki>st import TestCase''



''class TestTestCase(TestCase):''



''def test_test(self):''

''<nowiki>self.as</nowiki>sertEqual("this", "that")''

:* To run the tests: 
*:* open terminal
*:* cd to your directory
*:* and type “''<nowiki>manage.py</nowiki> test”''









#  Internationalization
## Label Strings:
* '''When you edit any code: Please label all strings that need to be translated later on!'''
* In html-files:
** Import: ''{% load i18n %}''
** Label: ''{% trans "MyString" %}''
* In Python-files:
** Import: ''from <nowiki>django.utils.tr</nowiki>anslation import ugettext as _''
** Label: ''_("MyString")''


*# Create .po file:
* All labelled strings are detected automatically and collected in a .po-file. This file is used for translations. 
* cd to .../repair$
* Type "''<nowiki>django-admin.py</nowiki> makemessages -l de''"  (This creates the .po-file for german language)
*# Translate .po-file (example):
* Before:

''    ''''#: templates<nowiki>/base.ht</nowiki>ml:5''

''    ''''msgid "Hello, this is built with Django Internationalization"''

''    ''''msgstr ""''

* After:

''    #: templates<nowiki>/base.ht</nowiki>ml:5''

''    ''''msgid "Hello, this is built with Django Internationalization"''

''msgstr "Hola, esto está construido con la Internacionalización de Django"''



