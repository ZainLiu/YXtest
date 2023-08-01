import base64
from Crypto.Cipher import AES


class AesEncrypt:
    # 密钥
    key = '0CoJUm6Qyw8W8jud'
    # 偏移量
    vi = '0102030405060708'

    def encrypt(self, data):
        """加密"""
        data = data.encode('utf8')
        data = (lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16).encode('utf-8'))(data)
        cipher = AES.new(self.key.encode('utf8'), AES.MODE_CBC, self.vi.encode('utf8'))
        encryptedbytes = cipher.encrypt(data)
        encodestrs = base64.b64encode(encryptedbytes)
        enctext = encodestrs.decode('utf8')
        return enctext

    def decrypt(self, data):
        """解密"""
        data = data.encode('utf8')
        encodebytes = base64.decodebytes(data)
        cipher = AES.new(self.key.encode('utf8'), AES.MODE_CBC, self.vi.encode('utf8'))
        text_decrypted = cipher.decrypt(encodebytes)
        unpad = lambda s: s[0:-s[-1]]
        text_decrypted = unpad(text_decrypted)
        text_decrypted = text_decrypted.decode('utf8')
        return text_decrypted


if __name__ == '__main__':
    # 注意点：加密数据中有中文的时候，会有问题
    data = "musen123"
    aes = AesEncrypt()
    # 加密
    enctext = aes.encrypt(data)
    print(enctext)
    # # 解密
    text_decrypted = aes.decrypt(enctext)
    print(text_decrypted)
