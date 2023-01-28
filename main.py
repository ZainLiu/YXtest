import hashlib

CLONE_NEWNS = 1
CLONE_NEWUTS = 2
CLONE_NEWIPC = 4
CLONE_NEWPID = 8
CLONE_NEWNET = 16
b = CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWPID | CLONE_NEWNET
flag = CLONE_NEWNS | CLONE_NEWUTS
c = flag & b
print(c)
print(bin(c))
d = 0b11
print(type(d))

print(hashlib.md5("PMS系统".encode(encoding='utf8')).hexdigest()[8:-8])
