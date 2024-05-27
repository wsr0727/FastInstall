import copy
import json
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
import base64
import hashlib
import time
import requests
import numpy as np

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')
"""
接口相关代码
"""

header_config = {
    "base": {"AppID": "512", "CHCode": "A001", "deviceOffset": "11", "OSVer": "8.1.0",
             "Lang": "zh", "DeviceType": "2", "TimeZone": "28800", "VerID": "12030104", "OSType": "2",
             "Country": "CN", "PlatForm": "11", "PlatForm2": "2", "PackageName": "com.sinyee.babybus.mathIII",
             "ProjectID": "530", "DeviceLang": "zh-CN",
             "statProductID": "2078", "CHID": "0", "IsFirstOpen": "0", "initGlobalVer": "6", "ProductID": "4034",
             "Appkey": "F1BFA20A1C734557A11F85EC55E3C412", "AppAge": "4", "IsDebug": "1",
             "OSSdkVer": "27", "AdAge": "5"},
    "platform": {"iPhone": {"PlatForm": "2", "PlatForm2": "1", "OSType": "1", "CHCode": "B001", "AppCHCode": "B001"},
                 "安卓": {"PlatForm": "11", "PlatForm2": "1", "OSType": "2", "CHCode": "A001", "AppCHCode": "A001"},
                 "iPad": {"PlatForm": "2", "PlatForm2": "1", "OSType": "1", "CHCode": "B002", "AppCHCode": "B002"},
                 "安卓平板": {"PlatForm": "12", "PlatForm2": "2", "OSType": "2", "CHCode": "A001", "AppCHCode": "A001"},
                 "谷歌": {"PlatForm": "60", "PlatForm2": "3", "OSType": "2", "CHCode": "A005", "AppCHCode": "A005"}
                 },
    "country": {"中国大陆": {"Country": "CN"},
                "美国": {"Country": "US"}
                },
    "language": {"简体": {"Lang": "zh"},
                 "英语": {"Lang": "en"}
                 },  # TODO 语言参数要换
    "version": {"VerID": "12030104"}
}

host_config = {"正式线": {"matrixdataapi": "https://matrixdataapi.babybus.com",
                         "packagedataapi": "https://packagedataapi.babybus.com"}}

path_config = {"首页": "/BabyMind/PageCenter/PageData",
               "子包信息": "/PackageData/GetPackageLangDataList"}

body_config = {"子包信息": {"加减": {
    "GECocos2DVerID": 1000000,
    "GEUnity2D": 0,
    "GEUnity3D": 0,
    "PackageResultList": [
        {
            "CategoryID": 1,
            "Lang": "",
            "PackageIdent": "MathTrainResource",
            "VerID": 0
        },
        {
            "CategoryID": 1,
            "Lang": "",
            "PackageIdent": "MathHappycounting",
            "VerID": 0
        },
        {
            "CategoryID": 1,
            "Lang": "",
            "PackageIdent": "math_workbook+-",
            "VerID": 0
        }
    ],
    "ResourceTypeCode": "X2"
}}}

query_config = {"base": ["AcceptVerID=1", "EncryptType=4", "geVerID=1000000"],
                "首页": ["routeCode=Index", "resourceTypeCode=X2"]}

args_common = {
    "思维正式": {"安卓-简体": {"platform": "安卓", "version": "", "language": "简体", "environment": "正式线",
                            "country": "中国大陆"},
               "谷歌-英语": {"platform": "谷歌", "version": "", "language": "英语", "environment": "正式线",
                            "country": "美国"},
               "苹果-简体": {"platform": "iPhone", "version": "", "language": "简体", "environment": "正式线",
                            "country": "中国大陆"}
                 }
}


def aes_decrypt(cipher_text):
    """
    AES解密
    :param cipher_text: 待解密的数据
    :return: 解密后的数据
    """
    # 解密
    aes_key = "U3EnojCQRlKT9Y0c"
    cipher = AES.new(aes_key.encode('utf-8'), AES.MODE_ECB)
    plaintext_bytes = cipher.decrypt(base64.b64decode(cipher_text))
    # 去除填充
    plaintext = unpad(plaintext_bytes, AES.block_size).decode('utf-8')
    return plaintext


def aes_encrypt(plaintext):
    """
    AES加密
    :param plaintext: 待加密的明文
    :return: 加密后的数据
    """
    aes_key = "U3EnojCQRlKT9Y0c"
    plaintext_bytes = pad(plaintext.encode('utf-8'), AES.block_size)  # 需要对明文进行补位操作
    cipher = AES.new(aes_key.encode('utf-8'), AES.MODE_ECB)
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


def get_PackageIdent_By_Pagedata(pagedata):
    """
    获取页面数据中的所有子包标识
    :param pagedata:页面数据
    :return package_idents:子包标识列表
    """
    package_idents = []
    for area in pagedata['data']['areaData']:
        for item in area['data']:
            package_idents.append(item['fieldData']['packageIdent'])
    return package_idents


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

    def header_complete(self):
        """
        组装数据
        :return: 完整的header参数
        """
        header = copy.deepcopy(header_config["base"])
        header.update(header_config["platform"][self.platform])
        header.update(header_config["country"][self.country])
        header.update(header_config["language"][self.language])
        header.update({"VerID": self.version.replace(".", "")})
        return header

    @staticmethod
    def query_complete(query, headers="", body=""):
        """
        组装数据
        :param query: 基础URL
        :param headers: 加密后的请求头
        :param body: 请求body
        :return: 完整URL
        """
        query = query + "&HeaderMD5=" + md5_encrypt(headers).upper() + "&ProductID=4034" + "&SignatureStamp=" + str(
            int(time.time()))
        if body:  # 有的接口没有body
            query = query + "&ContentMD5=" + md5_encrypt(body).upper()
        signature_md5 = md5_encrypt(query.lower() + "070b8be88f05434b910eca56aaf89154").upper()  # 所有查询参数计算出的MD5
        query = query + "&SignatureMD5=" + signature_md5
        logging.debug("query:" + query)
        return query

    def page_data_main(self):
        """
        首页接口
        :return:
        """
        header_encrypt = aes_encrypt(str(json.dumps(self.header_complete())))  # 请求头组装，并加密

        query_encrypt = self.query_complete("&".join(query_config["base"]), header_encrypt)

        url = host_config[self.environment]["matrixdataapi"] + path_config[
            "首页"] + "?" + query_encrypt
        # TODO 首页加上查询参数  query_config["首页"] 就会报错，签名失败。之后要请求其他页面了再优化
        logging.debug("URL:" + url + " header:" + str(header_encrypt))
        response = requests.request("GET", url, headers={'ClientHeaderInfo': header_encrypt})
        logging.debug("response:" + str(response.text))
        return response.json()

    @staticmethod
    def make_packagedata_body(package_idents, ge_cocos2d_ver_id="1000000", resource_type_code="X2"):
        """
        组装子包信息请求体
        :param package_idents: 子包标识列表
        :param ge_cocos2d_ver_id:
        :param resource_type_code:
        :return packagedata_body: 子包信息请求体
        """
        package_result_list = []
        for ident in package_idents:
            entry = {
                "PackageIdent": ident,
                "CategoryID": "1",
                "VerID": "100000"
            }
            package_result_list.append(entry)

        # 组装最终的 body 数据
        packagedata_body = {
            "GEUnity2D": 0,
            "GEUnity3D": 0,
            "GECocos2DVerID": ge_cocos2d_ver_id,
            "PackageResultList": package_result_list,
            "ResourceTypeCode": resource_type_code.lower()
        }
        return packagedata_body

    def packagedata(self, body):
        """
        获取子包信息
        :param body:请求体
        :return response:响应结果
        """
        header_encrypt = aes_encrypt(str(json.dumps(self.header_complete())))  # 请求头组装，并加密

        query_encrypt = self.query_complete("&".join(query_config["base"]), header_encrypt)

        content_encrypt = aes_encrypt(str(json.dumps(body)))

        url = host_config[self.environment]["packagedataapi"] + path_config[
            "子包信息"] + "?" + query_encrypt
        logging.debug("URL:" + url + " header:" + str(header_encrypt))
        response = requests.request("POST", url, headers={'ClientHeaderInfo': header_encrypt, 'Accept-Language': str(
            header_config["language"][self.language]["Lang"]) + "-"
                                                                                                                 +
                                                                                                                 header_config[
                                                                                                                     "country"][
                                                                                                                     self.country][
                                                                                                                     "Country"] + ";q=1"},
                                    data=content_encrypt)
        response = aes_decrypt(response.text)
        response = json.loads(response)
        logging.debug("response:" + json.dumps(response, ensure_ascii=False))
        return response


# 校验子包信息
class CheckPackageData:
    def __init__(self, package_data):
        self.package_data = package_data

    def is_exist_FileInfo(self):
        """
        :return result_arr: 子包信息校验结果（一个二维数组）
        """
        package_data = self.package_data
        # 获取 packageDataList 数组
        package_data_list = package_data.get('data', {}).get('packageDataList', [])

        result_arr = np.empty((0, 4))

        # 遍历 packageDataList
        for package in package_data_list:
            package_ident = package.get('packageIdent', 'N/A')
            title = package.get('title', 'N/A')
            lang_file_info = package.get('fileData').get('langFileInfo').get('fileMD5') if package.get('fileData',
                                                                                                       {}).get(
                'langFileInfo') else '语言包文件不存在'
            package_file_info = package.get('fileData').get('packageFileInfo').get('fileMD5') if package.get('fileData',
                                                                                                             {}).get(
                'packageFileInfo') else '子包文件不存在'

            # 打印每一行的数据
            # print(f"{package_ident:<25} {title:<25}{lang_file_info:<35} {package_file_info:<35}")
            row = [package_ident, title, lang_file_info, package_file_info]
            result_arr = np.append(result_arr, [row], axis=0)

        return result_arr


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


if __name__ == "__main__":
    # 代码调试
    args_ = args_common["思维正式"]["谷歌-英语"]
    data_requester = DataRequester(args_["platform"], "2050170", args_["language"], args_["environment"],
                                   args_["country"])
    body = data_requester.make_packagedata_body(["math_1andmany"], resource_type_code="X2")
    package_data = data_requester.packagedata(body)
    print(package_data)
# idents = get_PackageIdent_By_Pagedata(DataRequester("安卓", "2050101", "简体", "正式线", "中国大陆").page_data_main())
# body = make_packagedata_body(idents)
# DataRequester("安卓", "2050101", "简体", "正式线", "中国大陆").packagedata(body)
# print(DataRequester("安卓", "2050101", "简体", "正式线", "中国大陆").packagedata(body_config["子包信息"]["加减"]))
