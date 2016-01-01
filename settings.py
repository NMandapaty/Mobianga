'''
Created on Oct 8, 2012

@author: Nishant
'''
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')