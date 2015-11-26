u"""Creates a 3D image and plots it
"""

import numpy as np
import hyperspy.api as hs
import matplotlib.pyplot as plt

# Create an image stack with random data
im = hs.signals.Image(np.random.random((16, 32, 32)))

# Define the axis properties
im.axes_manager.signal_axes[0].name = u'X'
im.axes_manager.signal_axes[0].units = u'nm'
im.axes_manager.signal_axes[0].scale = 0.1
im.axes_manager.signal_axes[0].offset = 0

im.axes_manager.signal_axes[1].name = u'Y'
im.axes_manager.signal_axes[1].units = u'nm'
im.axes_manager.signal_axes[1].scale = 0.1
im.axes_manager.signal_axes[1].offset = 0

im.axes_manager.navigation_axes[0].name = u'time'
im.axes_manager.navigation_axes[0].units = u'fs'
im.axes_manager.navigation_axes[0].scale = 0.3
im.axes_manager.navigation_axes[0].offset = 100

# Give a title
im.metadata.General.title = u'Random image stack'

# Plot it
im.plot()

plt.show()  # No necessary when running in the HyperSpy's IPython profile
