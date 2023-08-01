import tensorflow as tf
import pandas as pd
import matplotlib.pyplot as plt
import os
import pylab

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# img_path = "./image/beauty001.jpg"
img_path = "./grayimg/0.jpg"
img = plt.imread(img_path)
print(img.shape)
print(img)
img2 = img

plt.imshow(img2)
print(img2)
pylab.show()

