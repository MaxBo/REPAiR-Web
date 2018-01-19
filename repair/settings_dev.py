from repair.settings import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
        'OPTIONS': {
             'timeout': 20,
         }
    },
}

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG, 
        'BUNDLE_DIR_NAME': 'bundles/dev/', 
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-dev.json'),
    }
}
