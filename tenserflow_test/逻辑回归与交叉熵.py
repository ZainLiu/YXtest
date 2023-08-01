import tensorflow as tf
import pandas as pd
import matplotlib.pyplot as plt
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# plt.scatter(x=data.newspaper, y=data.sales)
# plt.show()

data = pd.read_csv("./data_set/credit-a.csv", header=None)
print(data.head())

# print(data.iloc[:, -1].value_counts())
x = data.iloc[:, :-1]
y = data.iloc[:, -1].replace(-1, 0)
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(1000, input_shape=(15,), activation='relu'))
model.add(tf.keras.layers.Dense(1000, activation='relu'))
model.add(tf.keras.layers.Dense(1, activation='sigmoid'))
model.summary()
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["acc"])
history = model.fit(x, y, epochs=400)
# print(history.history.keys())
# plt.plot(history.epoch, history.history.get("acc"))
# plt.show()
test = data.iloc[-10:,:-1]
print(model.predict(test))

