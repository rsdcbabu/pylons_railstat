import os, sys
from paste.script.util.logging_config import fileConfig

baseDir='/home/deepak/pylons_railstat/railstat'
configFile = os.path.join(baseDir, 'production.ini')

sys.path.append(baseDir)
os.environ['PYTHON_EGG_CACHE'] = '/home/deepak/pylons_railstat/railstat/python-eggs'

fileConfig(configFile)

from paste.deploy import loadapp
application = loadapp('config:%s' % configFile)
