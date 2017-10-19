import hashlib


def md5(in_str):
    m = hashlib.md5()
    m.update(in_str.encode('utf-8'))
    return m.hexdigest()


def encode(in_str, salt):
    in_str = str(in_str)
    salt = str(salt)
    query = in_str + salt + md5(in_str)
    return md5(query)[-5:]