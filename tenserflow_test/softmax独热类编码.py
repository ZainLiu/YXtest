import tensorflow as tf
import pandas as pd
import numpy as np
import pylab
import matplotlib.pyplot as plt
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

(train_image, train_lable), (test_image, test_lable) = tf.keras.datasets.fashion_mnist.load_data()
# print(train_image.shape)
# print(train_lable[0])
# plt.imshow(train_image[0])
#
# pylab.show()
train_image = train_image / 255
test_image = test_image / 255
model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=(28, 28)),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(10, activation="softmax")
])
model.compile(optimizer=tf.keras.optimizers.Adam(lr=0.001), loss="sparse_categorical_crossentropy", metrics="acc")
model.fit(train_image, train_lable, epochs=10)
model.evaluate(test_image,test_lable)
