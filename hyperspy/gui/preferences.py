import traitsui.api as tui


class PreferencesHandler(tui.Handler):

    def close(self, info, is_ok):
        # Removes the span selector from the plot
        info.object.save()
        return True
preferences_view = tui.View(
    tui.Group(tui.Item(u'General', style=u'custom', show_label=False, ),
              label=u'General'),
    tui.Group(tui.Item(u'Model', style=u'custom', show_label=False, ),
              label=u'Model'),
    tui.Group(tui.Item(u'EELS', style=u'custom', show_label=False, ),
              label=u'EELS'),
    tui.Group(tui.Item(u'EDS', style=u'custom', show_label=False, ),
              label=u'EDS'),
    tui.Group(tui.Item(u'MachineLearning', style=u'custom',
                       show_label=False,),
              label=u'Machine Learning'),
    tui.Group(tui.Item(u'Plot', style=u'custom', show_label=False, ),
              label=u'Plot'),
    title=u'Preferences',
    handler=PreferencesHandler,)

eels_view = tui.View(
    tui.Group(
        u'synchronize_cl_with_ll',
        label=u'General'),
    tui.Group(
        u'eels_gos_files_path',
        u'preedge_safe_window_width',
        tui.Group(
            u'fine_structure_width',
            u'fine_structure_active',
            u'fine_structure_smoothing',
            u'min_distance_between_edges_for_fine_structure',
            label=u'Fine structure'),
        label=u'Model')
)
