u"""Creates a spectrum, and fits an arctan to it."""

import numpy as np
import hyperspy.api as hs

# Generate the data and make the spectrum
s = hs.signals.SpectrumSimulation(
    np.arctan(np.arange(-500, 500)))
s.axes_manager[0].offset = -500
s.axes_manager[0].units = u""
s.axes_manager[0].name = u"x"
s.metadata.General.title = u"Simple arctan fit"

s.add_gaussian_noise(0.1)

# Make the arctan component for use in the model
arctan_component = hs.model.components.Arctan()

# Create the model and add the arctan component
m = s.create_model()
m.append(arctan_component)

# Fit the arctan component to the spectrum
m.fit()

# Print the result of the fit
m.print_current_values()

# Plot the spectrum and the model fitting
m.plot()
