from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
import base64
import hashlib
import requests

"""
接口相关代码
"""

aes_key = "U3EnojCQRlKT9Y0c"

header = {"base": {"VerCode": "12.03.01.04", "AppID": "512", "AppPlatForm": "2", "CHCode": "A001", "deviceOffset": "11",
                   "OSVer": "8.1.0", "Lang": "zh", "DeviceType": "2", "TimeZone": "28800", "VerID": "12030104",
                   "OSType": "2",
                   "Country": "CN", "PlatForm": "11", "AppCHCode": "A001", "PlatForm2": "2",
                   "PackageName": "com.sinyee.babybus.mathIII", "ProjectID": "530", "DeviceLang": "zh-CN",
                   "statProductID": "2078", "CHID": "0", "IsFirstOpen": "0", "initGlobalVer": "6", "ProductID": "4034",
                   "AppLang": "zh-Hans-CN", "Appkey": "F1BFA20A1C734557A11F85EC55E3C412", "AppAge": "4", "IsDebug": "1",
                   "OSSdkVer": "27", "AdAge": "5"},

          }

host = {"releases": {"matrixdataapi": "https://matrixdataapi.babybus.com",
                     "packagedataapi": "https://packagedataapi.babybus.com"}}

path = {"首页": "/BabyMind/PageCenter/PageData",
        "子包信息": "/PackageData/GetPackageLangDataList"}

body = {"子包信息": {"GECocos2DVerID": 1000000, "GEUnity2D": 0, "GEUnity3D": 0, "PackageResultList": [
    {"CategoryID": 1, "Lang": "", "PackageIdent": "MathTrainResource", "VerID": 0}], "ResourceTypeCode": "X2"}}

query = {"首页": ["geVerID=1000000", "AcceptVerID=1", "routeCode=Index"]}


def aes_decrypt(cipher_text, key):
    """
    AES解密
    :param cipher_text: 待解密的数据
    :param key: 秘钥
    :return: 解密后的数据
    """
    # 解密
    cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    plaintext_bytes = cipher.decrypt(base64.b64decode(cipher_text))
    # 去除填充
    plaintext = unpad(plaintext_bytes, AES.block_size).decode('utf-8')
    return plaintext


def aes_encrypt(plaintext, key):
    """
    AES加密
    :param plaintext: 待加密的明文
    :param key: 秘钥
    :return: 加密后的数据
    """
    plaintext_bytes = pad(plaintext.encode('utf-8'), AES.block_size)  # 需要对明文进行补位操作
    cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    ciphertext_bytes = cipher.encrypt(plaintext_bytes)
    ciphertext = base64.b64encode(ciphertext_bytes).decode('utf-8')
    return ciphertext


def md5_encrypt(text):
    """
    计算MD5值
    :param text: 待计算的数据
    :return: MD5
    """
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()


class DataRequester:
    def __init__(self, platform, version, language, environment, country):
        """

        :param platform:
        :param version:
        :param language:
        :param environment:
        :param country:
        """
        self.platform = platform
        self.version = version
        self.language = language
        self.environment = environment
        self.country = country

    # def page_data(self):
    #     header


class RequestCheck:

    def task_control(self, platform, version, language, environment, country, url_type):
        """

        :param url_type:
        :param platform:
        :param version:
        :param language:
        :param environment:
        :param country:
        :return:
        """
        D = DataRequester(platform, version, language, environment, country)
        return True

# s = "5465131256415"
# ciphertext_str = "NO7t23VVX6J4sRYWvLOxW3Pe6sNHXGROMeOveS5qYM2wTEOCK6hfMn/JLMdPv7Mz"
# en_str = aes_encrypt(s, aes_key)
# print(en_str)
# decrypted_data = aes_decrypt(en_str, aes_key)
# print("解密:", decrypted_data)
# m1 = md5_encrypt(ciphertext_str)
# print(m1)
