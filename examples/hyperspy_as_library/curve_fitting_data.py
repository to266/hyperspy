u""" Loads hyperspy as a regular python library, loads spectrums from files, does curve fitting, and plotting the model and original spectrum to a png file"""

import hyperspy.api as hs
import matplotlib.pyplot as plt

coreLossSpectrumFileName = u"coreloss_spectrum.msa"
lowlossSpectrumFileName = u"lowloss_spectrum.msa"

s = hs.load(coreLossSpectrumFileName).to_EELS()
s.add_elements((u"Mn", u"O"))
s.set_microscope_parameters(
    beam_energy=300,
    convergence_angle=24.6,
    collection_angle=13.6)

ll = hs.load(lowlossSpectrumFileName).to_EELS()

m = s.create_model(ll=ll)
m.enable_fine_structure()
m.multifit(kind=u"smart")
m.plot()

plt.savefig(u"model_original_spectrum_plot.png")
