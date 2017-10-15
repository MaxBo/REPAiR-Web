1. mark strings:
----------------
- in html-files:
	{% load i18n %}		# import
	{% trans "MyString" %}  # marker
- in python-files:
	from django.utils.translation import ugettext as _    # import
	_("MyString") 		# marker


2. create .po file:
-------------------
- go to .../repair$
- type "django-admin.py makemessages -l de" 	# creates .po-file for german language


3. translate .po-file (example):
--------------------------------
before:
	#: templates/base.html:5
	msgid "Hello, this is built with Django Internationalization"
	msgstr ""
after:
	#: templates/base.html:5
	msgid "Hello, this is built with Django Internationalization"
	msgstr "Hola, esto está construido con la Internacionalización de Django"

4. Installation:
----------------
Install latest "Shared - 64 bit"-Version from
https://mlocati.github.io/articles/gettext-iconv-windows.html

Add gettext-folder to path
PATH=${PATH};C:\Program Files\gettext-iconv\bin