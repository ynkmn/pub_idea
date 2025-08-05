import numpy as np
a = np.array([1, 2, 2, 3, 4])
b = np.array([2, 3, 4, 5, 6])
res = np.intersect1d(a, b)
print(res)    # [2 3 4]
