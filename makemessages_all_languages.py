import os
from subprocess import Popen
from argparse import ArgumentParser

from django.core.management import execute_from_command_line


if __name__ == '__main__':
    parser = ArgumentParser()
    default_lang = ['de', 'nl', 'it', 'pl', 'hu']
    parser.add_argument('-l', '--locales', dest='locales',
                        nargs='*', default=default_lang)
    manage_py = os.path.join(os.path.dirname(__file__), 'manage.py')
    args = ['manage.py', 'makemessages', '-d', 'djangojs', '-e', 'html,js,py','-l']

    options = parser.parse_args()
    for locale in options.locales:
        execute_from_command_line(args + [locale])


