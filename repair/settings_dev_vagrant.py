from repair.settings import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
'default': {

        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'gdse_develop',
        'USER': 'postgres',
        'PASSWORD': 'wS9pgNkuyMub',
        'HOST': 'h2020repair.bk.tudelft.nl',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
            },
    },
#    'default': {
#        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
#        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
#        'OPTIONS': {
#             'timeout': 20,
#         }
#    },
}

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
GEOS_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/libgeos_c.so'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/dev/',
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-dev.json'),
    }
}
