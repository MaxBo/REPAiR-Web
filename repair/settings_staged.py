from repair.settings import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DB_NAME = 'gdse'
DB_USER = 'mypassword'
DB_PASS = 'gdse_staging_db'

DATABASES = {
    'default': {

        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'HOST': 'db',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
            },
    },
}

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/staged/',
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-staged.json'),
    }
}
