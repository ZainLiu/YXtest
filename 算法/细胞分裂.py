"""1 个细胞的生命周期是 3 小时，1 小时分裂一次。求 n 小时后，容器内有多少细胞"""
import hashlib


def rsa_decode(cipher_text):
    rsakey = RSA.importKey(private_key)  # 导入读取到的私钥
    cipher = Cipher_PKCS1_v1_5.new(rsakey)  # 生成对象
    # 将密文解密成明文，返回的是一个bytes类型数据，需要自己转换成str
    try:
        text = cipher.decrypt(base64.b64decode(cipher_text), "ERROR")
        return text.decode()
    except ValueError as e:
        pass
        return cipher_text
def md5(msg):
    return hashlib.md5(rsa_decode(password).encode(encoding='utf8')).hexdigest()


a = md5("YX2021!@#")
print(a)