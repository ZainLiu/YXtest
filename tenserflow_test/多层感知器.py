import tensorflow as tf
import pandas as pd

data = pd.read_csv("./data_set/Advertising.csv")
# print(data)
import matplotlib.pyplot as plt

plt.scatter(x=data.newspaper, y=data.sales)
plt.show()
x = data.iloc[:, 1:-1]
y = data.iloc[:, -1]
model = tf.keras.Sequential(
    [
        tf.keras.layers.Dense(10, input_shape=(3,),activation='relu',name="input",),
        tf.keras.layers.Dense(1,name="output")
    ]
)
model.summary()
model.compile(optimizer="adam",loss="mse")
model.fit(x,y,epochs=1000)
test = data.iloc[:10,1:-1]
print(model.predict(test))

