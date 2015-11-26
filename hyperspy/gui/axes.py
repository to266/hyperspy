
import traits.api as t
import traitsui.api as tui


def navigation_sliders(data_axes, title=None):
    u"""Raises a windows with sliders to control the index of DataAxis

    Parameters
    ----------
    data_axes : list of DataAxis instances

    """

    class NavigationSliders(t.HasTraits):
        pass

    nav = NavigationSliders()
    view_tuple = ()
    for axis in data_axes:
        name = unicode(axis).replace(u" ", u"_")
        nav.add_class_trait(name, axis)
        nav.trait_set([name, axis])
        view_tuple += (
            tui.Item(name,
                     style=u"custom",
                     editor=tui.InstanceEditor(
                         view=tui.View(
                             tui.Item(
                                 u"index",
                                 show_label=False,
                                 # The following is commented out
                                 # due to a traits ui bug
                                 # editor=tui.RangeEditor(mode="slider"),
                             ),
                         ),
                     ),
                     ),
        )

    view = tui.View(tui.VSplit(view_tuple), title=u"Navigation sliders"
                    if title is None
                    else title)

    nav.edit_traits(view=view)


data_axis_view = tui.View(
    tui.Group(
        tui.Group(
            tui.Item(name=u'name'),
            tui.Item(name=u'size', style=u'readonly'),
            tui.Item(name=u'index_in_array', style=u'readonly'),
            tui.Item(name=u'index'),
            tui.Item(name=u'value', style=u'readonly'),
            tui.Item(name=u'units'),
            tui.Item(name=u'navigate', label=u'navigate'),
            show_border=True,),
        tui.Group(
            tui.Item(name=u'scale'),
            tui.Item(name=u'offset'),
            label=u'Calibration',
            show_border=True,),
        label=u"Data Axis properties",
        show_border=True,),
    title=u'Axis configuration',)


def get_axis_group(n, label=u''):
    group = tui.Group(
        tui.Group(
            tui.Item(u'axis%i.name' % n),
            tui.Item(u'axis%i.size' % n, style=u'readonly'),
            tui.Item(u'axis%i.index_in_array' % n, style=u'readonly'),
            tui.Item(u'axis%i.low_index' % n, style=u'readonly'),
            tui.Item(u'axis%i.high_index' % n, style=u'readonly'),
            # The style of the index is chosen to be readonly because of
            # a bug in Traits 4.0.0 when using context with a Range traits
            # where the limits are defined by another traits_view
            tui.Item(u'axis%i.index' % n, style=u'readonly'),
            tui.Item(u'axis%i.value' % n, style=u'readonly'),
            tui.Item(u'axis%i.units' % n),
            tui.Item(u'axis%i.navigate' % n, label=u'slice'),
            show_border=True,),
        tui.Group(
            tui.Item(u'axis%i.scale' % n),
            tui.Item(u'axis%i.offset' % n),
            label=u'Calibration',
            show_border=True,),
        label=label,
        show_border=True,)
    return group
