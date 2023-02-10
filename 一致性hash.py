import binascii


def crc2hex(crc):
    """
    crc : str 从hex文件或bin文件中获取的有效数据
           func a2b_hex 16进制字符串 -> 二进制
           func crc32 二进制 计算得到crc值 -> int
           最后和 0xffffffff 相乘得正值
    return str 4个字节
    """
    # return '%08x' % (binascii.crc32(binascii.a2b_hex(crc)) & 0xffffffff)
    # 增加一个 取反
    return '%08x' % (binascii.crc32(binascii.a2b_hex(crc)) & 0xffffffff ^ 0xffffffff)

print(crc2hex(b"2"))