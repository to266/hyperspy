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
# along with  HyperSpy.  If not, see <http://www.gnu.org/licenses/>.import
# nose.tools


import nose.tools as nt

from hyperspy.misc.utils import attrsetter
from hyperspy.misc.utils import DictionaryTreeBrowser


class DummyThing(object):

    def __init__(self):
        self.name = u'Dummy'
        self.another = None

    def multiply(self):
        self.another = self.__class__()


class TestAttrSetter(object):

    def setUp(self):
        tree = DictionaryTreeBrowser(
            {
                u"Node1": {u"leaf11": 11,
                          u"Node11": {u"leaf111": 111},
                          },
                u"Node2": {u"leaf21": 21,
                          u"Node21": {u"leaf211": 211},
                          },
                u"Leaf3": 3
            })
        self.tree = tree
        self.dummy = DummyThing()

    def test_dtb_settattr(self):
        t = self.tree
        attrsetter(t, u'Node1.leaf11', 119)
        nt.assert_equal(t.Node1.leaf11, 119)
        attrsetter(t, u'Leaf3', 39)
        nt.assert_equal(t.Leaf3, 39)

    @nt.raises(AttributeError)
    def test_wrong_item(self):
        t = self.tree
        attrsetter(t, u'random.name.with.more.than.one', 13)

    def test_dummy(self):
        d = self.dummy
        d.multiply()
        attrsetter(d, u'another.name', u'New dummy')
        nt.assert_equal(d.another.name, u'New dummy')
        d.another.multiply()
        attrsetter(d, u'another.another.name', u'super New dummy')
        nt.assert_equal(d.another.another.name, u'super New dummy')
