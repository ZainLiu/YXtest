import json
from hashlib import md5

from ly_service.utils.RSA import rsa_encode
from ly_service.utils.Time import currentTime

a = {
    "logs": "gASViwAAAAAAAABdlCh9lCiMA3VpZJRNdwGMBHVzZXKUjAnolKHkv4rmloeUjAR0aW1llIwTMjAyMy0wMS0xMSAxMjoyOTo0MJSMBXN0YXRllIwM5Y+R6LW35a6h5om5lHV9lCiMBHRpbWWUjBMyMDIzLTAxLTExIDEyOjI5OjQwlIwFc3RhdGWUjAblroznu5OUdWUu",
    "node_ready": "gARdlC4="}

a = {
    'tpl_id': 58,
    'uid': 641,
    'username': "刘振宇",
    'params': {
        "level": 2
    }
}
print(json.dumps(a, ensure_ascii=False))


def create_secret(project_id, project_pw, app_name):
    """生成令牌"""
    # key
    secret_key_md5 = md5(f'{project_pw}_{app_name}_{currentTime()}'.encode())
    # sys + key + 项目ID + 应用名称
    secret_value = rsa_encode(f"sys_{secret_key_md5}_{project_id}_{app_name}")

    return secret_value


print(create_secret(1, "cf1420cd212b8761", "OPS系统"))
