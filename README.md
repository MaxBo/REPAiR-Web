[![CircleCI](https://circleci.com/gh/MaxBo/REPAiR-Web/tree/master.svg?style=shield&circle)](https://circleci.com/gh/MaxBo/REPAiR-Web/tree/master)
[![codecov](https://codecov.io/gh/MaxBo/REPAiR-Web/branch/master/graph/badge.svg)](https://codecov.io/gh/MaxBo/REPAiR-Web)

# REPAiR-Web Programmer’s Guide

## 1. Setting Up Django

-   Pull project from <https://github.com/MaxBo/REPAiR-Web>

-   *Optional: Create and activate a python-environment*

-   Register repair-package and Install dependencies with

*pip install -r requirements-dev.txt*

- On Windows:
*conda install -c conda-forge gdal=2.1
-   you have to add the spatialite directory to your PATH
-   in the settings.py the following environment variable has to be specified:
-   SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
-   the spatialite directory contains the mod_spatialite.dll
-   with its dependencies from
-   http://www.gaia-gis.it/gaia-sins/windows-bin-amd64/

-   the following dlls have to be exchanged from the ones from mingw
-   according to this blog
-   http://blog.jrg.com.br/2016/04/25/Fixing-spatialite-loading-problem/
-   rename libstdc++_64-6.dll to libstdc++_64-6.dll.original
-   copy libstdc++-6.dll form mingw and rename to libstdc++_64-6.dll
-   copy libgcc_s_seh-1.dll form mingw
-   rename libgcc_s_seh_64-1.dll to libgcc_s_seh_64-1.dll.original


-   Depending on your IDE you may have to set up the environment variable of the
    sitename manually (DJANGO_SITENAME=repair), e.g. in WingIDE under *Project
    Properties \> Environment*

-   Create a database based on used models with *python manage.py migrate*

-   Start the server on localhost with *python manage.py runserver
    \<port-number\>*

website is then accessible in browser via *localhost:\<port-number\>*

## 2. Or using Vagrant

Vagrant can set up the development evironment for you automatically. Essentially, it automates the management of virtual machines, thus you also need to have a virtualization provider (e.g. VirtualBox, VMware) installed. Then the REPAiR-Web server is set up and runs on a virtual machine (guest), completely isolated from your host. Yet, you can edit the source code on your host, with the same tools as normally, the code (actually the whole `REPAiR-Web` directory) is shared between the host and the guest. 

Once Vagrant is up and running, Django is listening at `http://localhost:8081` on the host.

## 2. Package/Folder Structure

**Packages**

| package                           | module      | description                                                                                                                   |
|-----------------------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------|
| repair                            | \-          | this is our base package including all the custom modules for running the server and client                                   |
|                                   | settings    | important file setting up the installed apps and the folder-structure (location of the template-directory, static files etc.) |
|                                   | urls        | maps the urls to functions called when accessing specific urls (relative to the base-url)                                     |
|                                   | wsgi        | specification for communication between server and web application (definitions are done in settings-module)                  |
| repair.apps                       | \-          | the web applications (aka subsites)                                                                                           |
| repair.apps.study_area            | \-          | example app (mapped in repair.urls to *\<base-url\>/study_area*)                                                              |
|                                   | urls        | maps the urls to functions (relative to *\<base-url\>/study_area*)                                                            |
|                                   | models      | the data required by the app, contains essential fields and behaviors of the data (stored in database)                        |
|                                   | serializers | definitions how to serialize the data (models) in order to communicate it between server and client                           |
|                                   | views       | definition of what to show client-side; render template on request and fill it with content (diagrams, texts etc.)            |
|                                   | tests       | Unit-tests of this app (see 4.)                                                                                               |
| repair.apps.study_area.migrations | \-          | definitions of how to store the models inside the database                                                                    |

**Paths and files** (packages not listed)

| path                                    | description                                                                                                                                      |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| /repair/locale                          | localizations of texts (see 5.)                                                                                                                  |
| /repair/templates                       | the templates for client-side rendering of pages (django-function get_template(‘’) is configured to point to this directory)                     |
| /repair/templates/base.html             | basic template all other templates which render subsites should derive from; contains the basic structure of the site and the navigation-bar     |
| /repair/templates/index.html            | the welcome page                                                                                                                                 |
| /repair/templates/study_area/index.html | the template used by the example app (see previous table)                                                                                        |
| /repair/static                          | static files required client-side like Javascript-scripts, images and fonts; accessible in code/html via constant variable *STATIC_URL*          |
| /repair/static/css                      | style-sheets for defining style of web-site when rendering templates client-side (ids, classes have to correspond to tags used in the templates) |
| /repair/static/fonts                    | fonts included in templates                                                                                                                      |
| /repair/static/img                      | images                                                                                                                                           |
| /repair/static/js                       | javascript libraries and scripts (see 3.)                                                                                                        |

## 3. Rest-API


-   see <https://en.wikipedia.org/wiki/Representational_state_transfer>

-   defined in django with the django-rest-framework (see
    <http://www.django-rest-framework.org/>)

-   provides serialized JSON-representations of resources (or html-views if
    accessing via browser)

-   API to be accessed by the javascripts on client-side (if you want to fill
    the django-templates directly you may ignore it and use the django-models
    instead)

-   url-entry-point is *\<website-adress\>*/api

-   the url represents resources inside the database (see next table)

-   List-routes of resources always interchange with a detailed Instance-route
    when progressing deeper (e.g. */api/casestudies/* shows you all casestudies
    and their attributes incl. the id, */api/casestudies/1* shows you the
    details of the casestudy with id 1)

-   deeper routes always have a relation to it’s predecessing subroutes (e.g.
    */api/casestudies/1/activities* show all activities of casestudy with id 1)

-   same resource-types may have different routes depending the relations they
    want to show with it’s route (e.g. */api/casestudies/\<id\>/activities* and
    */api/casestudies/\<id\>/activities*

-   the routes are defined in */repair/rest_urls.py*

## 3. Javascript Modularisation

-   the modularization is achieved by using django-require (post-processor for
    optimizing with RequireJS)

-   paths and variables for django-require are set up in repair.settings,
    require-path is set to */repair/static/js/*

-   organized as apps (analog to django-apps)

-   entry points for the apps are located in */repair/static/js/*

-   *\<app-name\>*.js is loaded in django-template via *{% require_module
    ‘\<app-name\>’ %}*

-   require-config.js defines all required javascript-modules and maps them to
    custom names; will load them on demand; all entry points have to require
    this file in order to be able to use the defined modules which are defined
    there

-   Backbone.js is used to organize data retrieved from the Rest-API and
    dynamically making views on the data and to interact with them (btw.
    Backbone takes heavy use of jQuery … meh :( )

**Paths and files**

| path                                 | description                                                                                                                                      |
|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| /repair/static/js/                   | base path for all javascripts                                                                                                                    |
| /repair/static/js/require-config.js  | definition of basic modules and aliases                                                                                                          |
| /repair/static/js/app-config.js      | constants shared across all apps (e.g. the urls of the rest-api), has to be required by specific app-modules in order to access the config there |
| /repair/static/js/libs               | 3rd party javascript libraries                                                                                                                   |
| /repair/static/js/app                | app-related scripts                                                                                                                              |
| /repair/static/js/app/models         | Backbone-models, each representing a resource of the rest-api                                                                                    |
| /repair/static/js/app/collections    | Backbone-collections of models (see /repair/static/js/models)                                                                                    |
| /repair/static/js/app/views          | Backbone-views for creating and swapping views on models/collections                                                                             |
| /repair/static/js/app/visualizations | visualizations created with javascript-libraries (e.g. Sankey-diagrams, maps)                                                                    |

### **a.  Backbone-Models/Collections**

-   a model that represents a single resource (a.k.a instance) in the Rest-API

-   collections hold an amount of models of the same type, represent lists of
    resources in the Rest-API

-   models and collections have to contain the API-url they are retrieved from /
    send to (stored in one place in the app-config for a better overview)

-   models/collections can be allocated via the new-Operator and then be fetched
    / deleted / posted from / to the Rest-API (see
    <http://backbonejs.org/#Model> respectively
    <http://backbonejs.org/#Collection> )

### **a.  Backbone-Views**

-   used client-side for dynamically creating and removing views on data

-   they always require the html-element to render them in and should receive a
    model/collection whose data they shall render and modify on demand (that’s
    the whole point of using them: click some data to view and change it)

-   they use the Underscore-template-engine, which is working similar to the
    django-template-engine but with slightly different syntax (see
    <http://underscorejs.org/#template> )

-   for localization/overview purposes you should put the templates directly
    into the django-template of the according app:

>   \<script type="text/template" id="..."\>

>   …

>   \</script\>

-   access the template via it’s id and get the inner html in order to pass it
    to the Underscore-template-engine

-   views should always be closed before replacing them, otherwise you get
    ‘ghost-views’ (define it yourself inside the view, see
    */repair/static/js/app/views/admin-edit-flows-view.js* for an example)

## 5. Continuous Development / Testing

### Workflow

>   **Don’t push directly into the master branch!**

1.  Checkout to new branch.

2.  Write a test.

3.  Write new Code and label strings for translation.

4.  Commit and push to your branch.

5.  Create pull-request on Github.

6.  Wait for CircleCi to test the code.

    1.  If build was successfull:

        1.  Merge your branch into master.

    2.  Else:

        1.  Fix the error, restart at 4., …

7.  Server automatically pulls master branch.

8.  Website is updated and you can start at 1. again.

Have a look at Workflow.pdf for further information.

### Automatic server updates via Webhook

    -   We use a Github-webhook to keep our website up-to-date. That means:
        Changes (push and pull requests) to the master-branch trigger a
        webhook-event, that is sent from github to
        <http://geodesignhub.h2020repair.bk.tudelft.nl/api/payload>. This event
        calls a function that automatically pulls the current master branch, so
        that our website is always up-to-date with the remote master branch.

### Continuous Integration with CircleCi

    -   We use Continuous Integration to test the code before it is merged to
        our master branch. This helps to detect errors before our website is
        updated with new code. Every time someone pushes new commits to any
        branch of our remote repository, CircleCi creates a build environment
        and runs our tests on their servers. This takes about 1-2 minutes. You
        can review the current build status here:
        <https://circleci.com/gh/MaxBo>. The github repository settings require
        a successful CircleCi-build in order to merge them to the master branch.
        This means: **No one (except MaxBo) can directly push any commits to our
        master branch.** If you want to commit something, create a new branch,
        commit and push to that branch and create a pull request. CircleCi
        automatically tests that branch and if all tests run successfully you
        can merge the new code from your branch to the master branch. For more
        information look at the Workflow section.

### Testing

    -   Django tests are directly written into the apps directory. For example:
        The tests for the study_area section are written into
        *../repair/apps/study_area/tests.py*.

    -   Basic structure:

>   *from django.test import TestCase*

>   *class TestTestCase(TestCase):*

>   *def test_test(self):*

>   *self.assertEqual("this", "that")*

-   To run the tests:

    -   open terminal

    -   cd to your directory

    -   and type “*manage.py test”*

## 6. Internationalization

### **a.  Label Strings**

    **When you edit any code: Please label all strings that need to be
    translated later on!**

-   In html-files:

    -   Import: *{% load i18n %}*

    -   Label: *{% trans "MyString" %}*

-   In Python-files:

    -   Import: *from django.utils.translation import ugettext as \_*

    -   Label: *\_("MyString")*

### **b.  Create .po file**

-   All labelled strings are detected automatically and collected in a .po-file.
    This file is used for translations.

-   cd to .../repair\$

-   Type "*django-admin.py makemessages -l de*" (This creates the .po-file for
    german language)

### **c.  Translate .po-file (example)**

-   Before:

>   *\#: templates/base.html:5*

>   *msgid "Hello, this is built with Django Internationalization"*

>   *msgstr ""*

-   After:

>   *\#: templates/base.html:5*

>   *msgid "Hello, this is built with Django Internationalization"*

>   *msgstr "Hola, esto está construido con la Internacionalización de Django"*
