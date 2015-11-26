import nose.tools
import numpy as np

from hyperspy.misc.utils import DictionaryTreeBrowser
from hyperspy.signal import Signal


class TestDictionaryBrowser(object):

    def setUp(self):
        tree = DictionaryTreeBrowser(
            {
                u"Node1": {u"leaf11": 11,
                          u"Node11": {u"leaf111": 111},
                          },
                u"Node2": {u"leaf21": 21,
                          u"Node21": {u"leaf211": 211},
                          },
            })
        self.tree = tree

    def test_add_dictionary(self):
        self.tree.add_dictionary({
            u"Node1": {u"leaf12": 12,
                      u"Node11": {u"leaf111": 222,
                                 u"Node111": {u"leaf1111": 1111}, },
                      },
            u"Node3": {
                u"leaf31": 31},
        })
        nose.tools.assert_equal(
            {u"Node1": {u"leaf11": 11,
                       u"leaf12": 12,
                       u"Node11": {u"leaf111": 222,
                                  u"Node111": {
                                      u"leaf1111": 1111},
                                  },
                       },
             u"Node2": {u"leaf21": 21,
                       u"Node21": {u"leaf211": 211},
                       },
             u"Node3": {u"leaf31": 31},
             }, self.tree.as_dictionary())

    def test_add_signal_in_dictionary(self):
        tree = self.tree
        s = Signal([1., 2, 3])
        s.axes_manager[0].name = u'x'
        s.axes_manager[0].units = u'ly'
        tree.add_dictionary({u"_sig_signal name": s._to_dictionary()})
        nose.tools.assert_is_instance(tree.signal_name, Signal)
        nose.tools.assert_true(np.all(
            tree.signal_name.data == s.data
        ))
        nose.tools.assert_equal(
            tree.signal_name.metadata.as_dictionary(),
            s.metadata.as_dictionary())
        nose.tools.assert_equal(
            tree.signal_name.axes_manager._get_axes_dicts(),
            s.axes_manager._get_axes_dicts())

    def test_signal_to_dictionary(self):
        tree = self.tree
        s = Signal([1., 2, 3])
        s.axes_manager[0].name = u'x'
        s.axes_manager[0].units = u'ly'
        tree.set_item(u'Some name', s)
        d = tree.as_dictionary()
        nose.tools.assert_true(np.all(d[u'_sig_Some name'][u'data'] == s.data))
        d[u'_sig_Some name'][u'data'] = 0
        nose.tools.assert_equal(
            {
                u"Node1": {
                    u"leaf11": 11,
                    u"Node11": {
                        u"leaf111": 111},
                },
                u"Node2": {
                    u"leaf21": 21,
                    u"Node21": {
                        u"leaf211": 211},
                },
                u"_sig_Some name": {
                    u'axes': [
                        {
                            u'name': u'x',
                            u'navigate': False,
                                    u'offset': 0.0,
                                    u'scale': 1.0,
                                    u'size': 3,
                                    u'units': u'ly'}],
                    u'data': 0,
                    u'learning_results': {},
                    u'metadata': {
                        u'General': {
                            u'title': u''},
                        u'Signal': {
                            u'binned': False,
                            u'record_by': u'',
                            u'signal_origin': u'',
                            u'signal_type': u''},
                        u'_HyperSpy': {
                            u'Folding': {
                                u'original_axes_manager': None,
                                u'original_shape': None,
                                u'unfolded': False,
                                u'signal_unfolded': False}}},
                    u'original_metadata': {},
                    u'tmp_parameters': {}}},
            d)
