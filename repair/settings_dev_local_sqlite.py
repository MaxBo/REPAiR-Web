from repair.settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
    },

}

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
DEBUG = True

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/dev/',
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-dev.json'),
    }
}
