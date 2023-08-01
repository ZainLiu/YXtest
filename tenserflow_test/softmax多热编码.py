import tensorflow as tf
import pandas as pd
import numpy as np
import pylab
import matplotlib.pyplot as plt
import os
from skimage import transform


os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def get_img():
    path = './image/shoes03.jpg'
    x = plt.imread(path).astype('float32')
    # plt.imshow(x.astype('int'))
    # plt.show()
    # print(x)
    final_x = []
    for i in x:
        final_y = []
        for j in i:
            d = j[0] * 0.299 + j[1] * 0.587 + j[2] * 0.114
            final_y.append(d)
        final_x.append(final_y)
    # print(final_x)
    final = np.array(final_x)
    # print(final.argmin())
    dst = transform.resize(final, (28, 28))
    # print(dst)
    # plt.imshow(gray.astype('int'))
    #
    # plt.show()
    plt.imshow(dst.astype('int'))
    # print(dst)
    # plt.savefig('./grayimg/1')
    plt.show()
    return dst

(train_image, train_lable), (test_image, test_lable) = tf.keras.datasets.fashion_mnist.load_data()
# print(train_image.shape)
# print(train_lable[0])
# plt.imshow(train_image[0])
#
# pylab.show()
train_image = train_image / 255
test_image = test_image / 255
train_lable_multihot = tf.keras.utils.to_categorical(train_lable)
test_lable_multihot = tf.keras.utils.to_categorical(test_lable)
model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=(28, 28)),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(10, activation="softmax")
])
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics="acc")
model.fit(train_image, train_lable_multihot, epochs=5)
model.evaluate(test_image,test_lable_multihot)

# predict = model.predict(test_image)
# print(predict.shape)
# print(predict[0])
# print(np.argmax(predict[0]))
#
# print(test_lable_multihot[0])
# plt.imshow(test_image[0])
# pylab.show()


shoes_img = get_img()
print(shoes_img)
predict = model.predict(np.array([shoes_img]))
print(predict[0])