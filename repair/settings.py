"""
Django settings for repair project.

Generated by 'django-admin startproject' using Django 1.11.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
from django.utils.translation import ugettext_lazy as _

DEBUG = False

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_ROOT = os.path.abspath(os.path.join(PROJECT_DIR, 'public'))

# The baseUrl to pass to the r.js optimizer.
REQUIRE_BASE_URL = 'js'

# The name of the build profile for the site, relative to REQUIRE_BASE_URL.
# Leave blank to use the built-in default build profile.
REQUIRE_BUILD_PROFILE = 'app.build.js'

# The name of the require.js script used by your project, relative to
# REQUIRE_BASE_URL.
REQUIRE_JS = os.path.join('libs', 'require.js')

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = DEBUG

## A dictionary of standalone modules to build with almond.js.
#REQUIRE_STANDALONE_MODULES = {
    #'app': {
        ## Where to output the built module, relative to REQUIRE_BASE_URL.
        #'out': 'app.min.js',

        ## A build profile used to build this standalone module.
        #'build_profile': REQUIRE_BUILD_PROFILE,
    #}
#}

# A tuple of files to exclude from the compilation result of r.js.
REQUIRE_EXCLUDE = (
    'build.txt',
    os.path.join(REQUIRE_BASE_URL, REQUIRE_BUILD_PROFILE),
)

# The file storage engine to use when collecting static files with the
# `collectstatic` management command.
#STATICFILES_STORAGE = 'require.storage.OptimizedStaticFilesStorage'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$f#=dn^_6xu1e7py@$(8_8yu2(%*a&b@6uxr*_zyi3c*%5@u1^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['geodesignhub.h2020repair.bk.tudelft.nl',
                 'gdse.h2020repair.bk.tudelft.nl',
                 "localhost",
                 "127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'repair.apps.login',
    'repair.apps.asmfa',
    'repair.apps.studyarea',
    'repair.apps.changes',
    'repair.apps.statusquo',
    'require'
]

#SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_AUTHENTIFICATION_CLASSES': [],
    'PAGE_SIZE': 10,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'repair.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.static',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'repair.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
    },

}

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_REDIRECT_URL = '/'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('en-us', _('English')),
    ('de', _('German')),
    ('nl', _('Dutch')),
    ('pl', _('Polish')),
    ('hu', _('Hungarian')),
    ('it', _('Italian')),
)

if os.name == 'posix':
    GDAL_LIBRARY_PATH = os.path.join(sys.exec_prefix,
                                     'lib', 'libgdal.so')
    GEOS_LIBRARY_PATH = os.path.join(sys.exec_prefix,
                                     'lib', 'libgeos_c.so')
    PROJ4_LIBRARY_PATH = os.path.join(sys.exec_prefix,
                                     'lib', 'libproj.so')

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, "locale"),
)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

# dir of static files for deployment
STATIC_ROOT = os.path.join(PUBLIC_ROOT, 'static')
MEDIA_ROOT = os.path.join(PUBLIC_ROOT, 'media')

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static")
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
