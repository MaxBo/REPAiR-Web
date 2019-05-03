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

SPATIALITE_LIBRARY_PATH = 'mod_spatialite.so'
GEOS_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/libgeos_c.so'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/staged/',
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-staged.json'),
    }
}
