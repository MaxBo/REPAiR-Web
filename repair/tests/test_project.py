from django.conf import settings

def pytest_configure():
    settings.configure(DJANGO_SETTINGS_MODULE = test_settings)

def test_dummy():
    assert True
