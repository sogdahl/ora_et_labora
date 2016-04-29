"""
WSGI config for test_angular project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import sys, os

INTERP = "/home/oraetlabora/opt/python-2.7.11/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

cwd = os.getcwd()
sys.path.append(cwd)
sys.path.append(os.path.join(cwd, 'ora_et_labora'))

sys.path.insert(0, os.path.join(cwd, 'env', 'bin'))
sys.path.insert(0, os.path.join(cwd, 'env', 'lib', 'python2.7', 'site-packages', 'django'))
sys.path.insert(0, os.path.join(cwd, 'env', 'lib', 'python2.7', 'site-packages'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ora_et_labora.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
