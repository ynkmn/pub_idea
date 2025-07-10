import numpy as np

z_widths = np.array([0.2, 0.3, 0.5])
z_heights = np.concatenate(([0], np.cumsum(z_widths)[:-1]))
print(z_heights)  # [0.  0.2 0.5]
