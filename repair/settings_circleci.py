from repair.settings import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'circle_test',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/dev/',
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-dev.json'),
    }
}

FIXTURE_DIRS.append(os.path.join(PROJECT_DIR, "graph_fixtures"),)