import nose.tools

from hyperspy.misc.utils import slugify


def test_slugify():
    nose.tools.assert_equal(slugify(u'ab !@#_ ja &(]'), u'ab___ja')
