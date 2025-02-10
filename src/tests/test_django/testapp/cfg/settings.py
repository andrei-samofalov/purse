"""
Django settings for testapp project.
"""
import os
from pathlib import Path

os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ['PATH'] = os.getcwd() + os.pathsep + os.environ['PATH']
SECRET_KEY = 'django-insecure-arv%wu6@j_k9rltlo*_rza4)xc65+*8yk(ci#@ma5mugl8ne8i'
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tests.test_django.testapp.users.apps.UsersConfig',
]
MIDDLEWARE = []
TEMPLATES = []
# WSGI_APPLICATION = 'cfg.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = False
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
