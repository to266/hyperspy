import nose.tools

from hyperspy.drawing.figure import BlittedFigure


def test_title_length():
    f = BlittedFigure()
    f.title = u"Test" * 50
    nose.tools.assert_less(max(
        [len(line) for line in f.title.split(u"\n")]), 61)
