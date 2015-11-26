

import nose.tools


from hyperspy.misc.eds.utils import get_xray_lines_near_energy


def test_xray_lines_near_energy():
    E = 1.36
    lines = get_xray_lines_near_energy(E)
    nose.tools.assert_list_equal(
        lines,
        [u'Pm_M2N4', u'Ho_Ma', u'Eu_Mg', u'Se_La', u'Br_Ln', u'W_Mz', u'As_Lb3',
         u'Kr_Ll', u'Ho_Mb', u'Ta_Mz', u'Dy_Mb', u'As_Lb1', u'Gd_Mg', u'Er_Ma',
         u'Sm_M2N4', u'Mg_Kb', u'Se_Lb1', u'Ge_Lb3', u'Br_Ll', u'Sm_Mg', u'Dy_Ma',
         u'Nd_M2N4', u'As_La', u'Re_Mz', u'Hf_Mz', u'Kr_Ln', u'Er_Mb', u'Tb_Mb'])
    lines = get_xray_lines_near_energy(E, 0.02)
    nose.tools.assert_list_equal(lines, [u'Pm_M2N4'])
    E = 5.4
    lines = get_xray_lines_near_energy(E)
    nose.tools.assert_list_equal(
        lines,
        [u'Cr_Ka', u'La_Lb2', u'V_Kb', u'Pm_La', u'Pm_Ln', u'Ce_Lb3', u'Gd_Ll',
         u'Pr_Lb1', u'Xe_Lg3', u'Pr_Lb4'])
    lines = get_xray_lines_near_energy(E, only_lines=(u'a', u'b'))
    nose.tools.assert_list_equal(
        lines,
        [u'Cr_Ka', u'V_Kb', u'Pm_La', u'Pr_Lb1'])
    lines = get_xray_lines_near_energy(E, only_lines=(u'a'))
    nose.tools.assert_list_equal(
        lines,
        [u'Cr_Ka', u'Pm_La'])
