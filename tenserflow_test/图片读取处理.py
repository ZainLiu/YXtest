from matplotlib import pyplot as plt
import numpy as np
from skimage import transform


def get_img():
    path = './image/shoes01.jpg'
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
    gray = x
    # print(final_x)
    final = np.array(final_x)
    # print(final.argmin())
    dst = transform.resize(final, (28, 28))
    # print(dst)
    print(dst.shape)
    # plt.imshow(gray.astype('int'))
    #
    # plt.show()
    plt.imshow(dst.astype('int'))
    print(dst)
    # plt.savefig('./grayimg/1')
    plt.show()
    return dst


if __name__ == '__main__':
    get_img()
