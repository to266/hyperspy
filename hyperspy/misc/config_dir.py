# -*- coding: utf-8 -*-
# Copyright 2007-2015 The HyperSpy developers
#
# This file is part of  HyperSpy.
#
#  HyperSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  HyperSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with  HyperSpy.  If not, see <http://www.gnu.org/licenses/>.

import os
import os.path
import shutil
from hyperspy import messages

config_files = list()
data_path = os.sep.join([os.path.dirname(__file__), u'..', u'data'])

if os.name == u'posix':
    config_path = os.path.join(os.path.expanduser(u'~'), u'.hyperspy')
    os_name = u'posix'
elif os.name in [u'nt', u'dos']:
    ##    appdata = os.environ['APPDATA']
    config_path = os.path.expanduser(u'~/.hyperspy')
# if os.path.isdir(appdata) is False:
# os.mkdir(appdata)
##    config_path = os.path.join(os.environ['APPDATA'], 'hyperspy')
    os_name = u'windows'
else:
    messages.warning_exit(u'Unsupported operating system: %s' % os.name)

if os.path.isdir(config_path) is False:
    messages.information(u"Creating config directory: %s" % config_path)
    os.mkdir(config_path)

for file in config_files:
    templates_file = os.path.join(data_path, file)
    config_file = os.path.join(config_path, file)
    if os.path.isfile(config_file) is False:
        messages.information(u"Setting configuration file: %s" % file)
        shutil.copy(templates_file, config_file)
