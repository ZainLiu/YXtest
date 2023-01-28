# coding:utf-8

import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as Signature_PKCS1_v1_5
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
from Crypto.Hash import SHA


private_key = '''-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCW1QCPJPnzTHgbdMdqPiwcksXhUJsQZjf6J/VtosxVqMP2SUB/
FdFU8aMw0+XgPhUS3pcmFKU1JGjlEUnW3I3aPYOx0FTrQbUcv8jl8UIM59vyXAp7
0nXi1Dq9CVZ7q6fQyuwIz7ZQWUEEhyTTW7QP+ktISmLrXqnCfn+hDylk5wIDAQAB
AoGAA3KW8q6rr+39iNMgg8MsCvMn5sCK6tMLUIJ9T6Y6+XJEGGsQOFdtU326dzFA
veFtZeMEnXA3XoGYjDPa9jhQXbWyTzndmrIpv2KXOy/3tis2rUtuRExxpNDuk2mY
YETGdnCRxRaDlrCF1qlXY8b8EVRKsBtGtJJ3A4ze+ZpmvIECQQDBoGdTEQT7fRbq
EvZukxBa1FVg7tgDjOvMfw4LtLwc2LxRWeDwMdE+0Xr8JEduHk8TLNr0opRu72aJ
wAU4qanHAkEAx2uB1EeQLubBE8+bkToSRG0JpsLSK4tw81RnhxEx3EUhoNdBdXKE
jYdCl0w7iy0cyFrbDi287m56vJr0z0Nr4QJAN9MWVyWuCQ/8nkoPULwH2Bgl8YeL
MiLcDR6InylhnvOB//Zo2veR+4mL6sxO59nHNKEXE7cYEo/lQUvidX69GwJAXDtt
3aeHmRmivS3tDpskLb+ckiNTH06r2+7yvvaF8BGNPx2vqclgYzDm7KEWfQVNZaEX
5ZPj6Qbx/19P0LinIQJBAIQGzueE2R4zWQoo6RENwt7GGuyMRJNd992DOBVocNu+
r3HSWr0pybO9eqCQvqvqfNPF85x4RqUa7waXuq/TZiM=
-----END RSA PRIVATE KEY-----'''

publice_key = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCW1QCPJPnzTHgbdMdqPiwcksXh
UJsQZjf6J/VtosxVqMP2SUB/FdFU8aMw0+XgPhUS3pcmFKU1JGjlEUnW3I3aPYOx
0FTrQbUcv8jl8UIM59vyXAp70nXi1Dq9CVZ7q6fQyuwIz7ZQWUEEhyTTW7QP+ktI
SmLrXqnCfn+hDylk5wIDAQAB
-----END PUBLIC KEY-----'''

'''*RSA签名
* data待签名数据
* 签名用商户私钥，必须是没有经过pkcs8转换的私钥
* 最后的签名，需要用base64编码
* return Sign签名
'''
def rsa_sign(data):
    key = RSA.importKey(private_key)
    h = SHA.new(data.encode("utf8"))
    signer = Signature_PKCS1_v1_5.new(key)
    signature = signer.sign(h)
    return base64.b64encode(signature)


'''*RSA验签
* data待签名数据
* signature需要验签的签名
* 验签用支付宝公钥
* return 验签是否通过 bool值
'''
def rsa_verify(data, signature):
    key = RSA.importKey(publice_key)
    h = SHA.new(data.encode("utf8"))
    verifier = Signature_PKCS1_v1_5.new(key)
    if verifier.verify(h, base64.b64decode(signature)):
        return True
    return False


# 公钥加密
def rsa_encode(message):
    rsakey = RSA.importKey(publice_key)  # 导入读取到的公钥
    cipher = Cipher_PKCS1_v1_5.new(rsakey)  # 生成对象
    # 通过生成的对象加密message明文，注意，在python3中加密的数据必须是bytes类型的数据，不能是str类型的数据
    cipher_text = base64.b64encode(
        cipher.encrypt(message.encode("utf8")))
    # 公钥每次加密的结果不一样跟对数据的padding（填充）有关
    return cipher_text.decode()


# 私钥解密
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


if __name__ == "__main__":
    token = "HwVayuW7cxi45cAj+N8kMdbgoYDMS/PhKRNdAd1WPQa5cj/Wqp+lzBHZb/EwnkcGmn/w2CfjicfvtuSxe1bRmcQPopHI/+rgmn/JLlgOfTR+A3IdTDdXvP3bt9NhzGEDheFJp3iaaKfRJzOypMpmN4WEdA5CRW1p/Jj/Nn9GvYw="
    token_obj = rsa_decode(token)
    print(token_obj)
