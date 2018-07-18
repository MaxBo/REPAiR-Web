from repair.settings import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DB_USER = 'postgres'
DB_PASS = ''
DB_NAME = 'gdse_db'
DB_HOST = 'db'
DB_PORT = '5432'

DATABASES = {
    'default': {

        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        #'OPTIONS': {
            #'sslmode': 'require',
            #},
    },
}

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/staged/',
        'STATS_FILE': os.path.join(PROJECT_DIR, 'webpack-stats-staged.json'),
    }
}
