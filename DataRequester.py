import copy
import json
import logging
from tkinter import messagebox
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
import base64
import hashlib
import time
import requests
import numpy as np
import os

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
                 "鸿蒙": {"PlatForm": "80", "PlatForm2": "14", "OSType": "6", "CHCode": "E023", "AppCHCode": "E023"},
                 "谷歌": {"PlatForm": "60", "PlatForm2": "3", "OSType": "2", "CHCode": "A005", "AppCHCode": "A005"}
                 },
    "country": {"中国大陆": {"Country": "CN"},
                "香港": {"Country": "HK"},
                "澳门": {"Country": "MO"},
                "台湾": {"Country": "TW"},
                "美国": {"Country": "US"},
                "加拿大": {"Country": "CA"},
                "澳大利亚": {"Country": "AU"},
                "巴西": {"Country": "BR"},
                "德国": {"Country": "DE"},
                "法国": {"Country": "FR"},
                "英国": {"Country": "GB"},
                "印度": {"Country": "IN"},
                "日本": {"Country": "JP"},
                "韩国": {"Country": "KR"},
                "墨西哥": {"Country": "MX"},
                "俄罗斯": {"Country": "RU"},
                "南非": {"Country": "ZA"},
                "意大利": {"Country": "IT"},
                "西班牙": {"Country": "ES"},
                "沙特阿拉伯": {"Country": "SA"},
                "阿根廷": {"Country": "AR"},
                "土耳其": {"Country": "TR"},
                "瑞士": {"Country": "CH"},
                "瑞典": {"Country": "SE"},
                "荷兰": {"Country": "NL"},
                "新加坡": {"Country": "SG"},
                "新西兰": {"Country": "NZ"},
                "挪威": {"Country": "NO"},
                "比利时": {"Country": "BE"},
                "芬兰": {"Country": "FI"},
                "丹麦": {"Country": "DK"},
                "爱尔兰": {"Country": "IE"},
                "奥地利": {"Country": "AT"},
                "伊朗": {"Country": "IR"},
                "以色列": {"Country": "IL"},
                "埃及": {"Country": "EG"},
                "阿联酋": {"Country": "AE"},
                "马来西亚": {"Country": "MY"},
                "泰国": {"Country": "TH"},
                "菲律宾": {"Country": "PH"},
                "印度尼西亚": {"Country": "ID"},
                "越南": {"Country": "VN"},
                "乌克兰": {"Country": "UA"},
                "波兰": {"Country": "PL"},
                "匈牙利": {"Country": "HU"},
                "罗马尼亚": {"Country": "RO"},
                "捷克": {"Country": "CZ"},
                "希腊": {"Country": "GR"},
                "葡萄牙": {"Country": "PT"},
                "乌拉圭": {"Country": "UY"},
                "智利": {"Country": "CL"},
                "埃塞俄比亚": {"Country": "ET"},
                "肯尼亚": {"Country": "KE"},
                "尼日利亚": {"Country": "NG"},
                "摩洛哥": {"Country": "MA"},
                "哥伦比亚": {"Country": "CO"},
                "秘鲁": {"Country": "PE"},
                "委内瑞拉": {"Country": "VE"}
                },
    "language": {"简体": {"Lang": "zh"},
                 "英语": {"Lang": "en"},
                 "繁体": {"Lang": "zht"},
                 "日语": {"Lang": "ja"},
                 "韩语": {"Lang": "ko"},
                 "葡萄牙语": {"Lang": "pt"},
                 "俄语": {"Lang": "ru"},
                 "越南语": {"Lang": "vi"},
                 "泰语": {"Lang": "th"},
                 "阿拉伯语": {"Lang": "ar"},
                 "西班牙语": {"Lang": "es"},
                 "法语": {"Lang": "fr"},
                 "印度尼西亚语": {"Lang": "id"}
                 },  # TODO 语言参数要换
    "version": {"VerID": "12030104"}

}

host_config = {"正式线": {"matrixdataapi": "https://matrixdataapi.babybus.com",
                          "packagedataapi": "http://packagedataapi.babybus.com",
                          "manage": "https://manage.mm.babybus.com"
                          },
               "测试线": {"matrixdataapi": "https://matrixdataapi.development.platform.babybus.com",
                          "packagedataapi": "https://packagedataapi.development.platform.babybus.com",
                          "manage": "https://manage.tm.babybus.com"
                          }
               }

path_config = {"首页": "/BabyMind/PageCenter/PageData",
               "非首页": "/PageCenter/PageData",
               "子包信息": "/PackageData/GetPackageLangDataList",
               "分包信息": "/PackageDataManage/SubPackageInfo/ReadData"
               }

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
                "首页": ["resourceTypeCode=X2", "routeCode=Index2"],
                "脑力开发": ["resourceTypeCode=X2", "routeCode=Expand"],
                "入园准备": ["resourceTypeCode=X2", "routeCode=School"],
                "巩固练习": ["resourceTypeCode=X2", "routeCode=Train2"],
                "加减专项": ["resourceTypeCode=X2", "routeCode=Arithmetic2"],
                "思维视频": ["resourceTypeCode=X2", "routeCode=Video"],
                "亲子互动": ["resourceTypeCode=X2", "routeCode=Interaction"]
                }

args_common = {
    "思维正式": {"安卓-简体": {"platform": "安卓", "version": "", "language": "简体", "environment": "正式线",
                               "country": "中国大陆"},
                 "谷歌-英语": {"platform": "谷歌", "version": "", "language": "英语", "environment": "正式线",
                               "country": "美国"},
                 "苹果-简体": {"platform": "iPhone", "version": "", "language": "简体", "environment": "正式线",
                               "country": "中国大陆"},
                 "苹果-英语": {"platform": "iPhone", "version": "", "language": "英语", "environment": "正式线",
                               "country": "美国"},
                 "鸿蒙-简体": {"platform": "鸿蒙", "version": "", "language": "简体", "environment": "正式线",
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


def download_file(url, save_path):
    """
    下载文件
    :param url:下载地址
    :param save_path:保存的位置
    :return save_path:下载成功，返回保存的位置
    """
    # 创建文件目录（如果不存在）
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.debug(f"文件已成功下载到： {save_path}")
        return save_path
    else:
        logging.debug(f"下载失败，状态码: {response.status_code}")


def get_PackageIdent_By_Pagedata(pagedata):
    """
    获取页面数据中的所有子包标识
    :param pagedata:页面数据
    :return package_idents:子包标识列表
    """
    package_idents = []
    for area in pagedata['data']['areaData']:
        for item in area['data']:
            if item['dataCode'] != 'ConfigData':
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
    def query_complete(query="", headers="", body=""):
        """
        组装数据
        :param query: 查询参数
        :param headers: 加密后的请求头
        :param body: 请求body
        :return: 完整URL
        """
        if query:
            query = "&" + query
        query = "&".join(query_config["base"]) + "&HeaderMD5=" + md5_encrypt(
            headers).upper() + "&ProductID=4034" + query + "&SignatureStamp=" + str(
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

        query_encrypt = self.query_complete("&".join(query_config["首页"]), header_encrypt)

        url = host_config[self.environment]["matrixdataapi"] + path_config[
            "首页"] + "?" + query_encrypt

        logging.debug("URL:" + url + " header:" + str(header_encrypt))
        response = requests.request("GET", url, headers={'ClientHeaderInfo': header_encrypt, 'Accept-Language': str(
            header_config["language"][self.language]["Lang"]) + "-" + header_config["country"][self.country][
                                                                                                                    "Country"] + ";q=1"})
        logging.debug("response:" + str(response.text))
        return response.json()

    def page_data(self, route):
        """
        脑力开发、加减专项、思维视频、巩固练习、亲子互动页面数据
        :param route: 获取的位置
        :return: 页面数据
        """
        header_encrypt = aes_encrypt(str(json.dumps(self.header_complete())))  # 请求头组装，并加密

        query_encrypt = self.query_complete("&".join(query_config[route]), header_encrypt)

        url = host_config[self.environment]["matrixdataapi"] + path_config[
            "非首页"] + "?" + query_encrypt

        logging.debug("URL:" + url + " header:" + str(header_encrypt))
        response = requests.request("GET", url, headers={'ClientHeaderInfo': header_encrypt, 'Accept-Language': str(
            header_config["language"][self.language]["Lang"]) + "-" + header_config["country"][self.country][
                                                                                                                    "Country"] + ";q=1"})
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

        query_encrypt = self.query_complete(headers=header_encrypt)

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

    def get_subpackage_page_data(self, PackageID):
        """
        获取后台分包页面信息
        :param cookies:
        :return:
        """
        from CookiesFetcher import load_cookies, get_cookies_from_browser, save_cookies

        # 加载Cookie
        cookies = load_cookies()

        # 如果没有Cookie，则获取新的Cookie
        if cookies is None:
            cookies = get_cookies_from_browser(host_config[self.environment]["manage"])
            save_cookies(cookies)

        url = host_config[self.environment]["manage"] + path_config["分包信息"]
        params = {
            'Power_MenuCoteID': '1',
            'Power_MenuDocumentID': '302',
            'Power_MenuID': '5abe073aa34648fab985c2f68f733ce0',
            'Power_ModalType': 'Modal',
            'Transfer_PackageID': PackageID
        }
        # 构建请求的会话
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        # 发起请求
        response = session.post(url, params=params)

        if response.json().get("ResultMessage") == "不好意思，您登录超时，请重新登录":
            messagebox.showinfo("提示", "登录超时，需要重新获取Cookie...")
            cookies = get_cookies_from_browser(host_config[self.environment]["manage"])
            save_cookies(cookies)
            return self.get_subpackage_page_data(PackageID)
        return response.json()


class PackageData:
    def __init__(self, package_data):
        self.package_data = package_data

    def get_packageID_by_packagedata(self):
        """
        从子包信息中提取子包ID
        :return: 子包ID
        """
        package_data = self.package_data
        package_id = package_data['data']['packageDataList'][0]['packageID']
        return package_id


class PageData:
    def __init__(self, page_data):
        self.page_data = page_data

    def get_age_config_by_expanddata(self):
        """
        从脑力开发页面配置中获取年龄配置
        :return  result:年龄配置二位数组
        """
        # 初始化结果数组
        result = np.empty((0, 8))
        class_id = {"2": "入园准备", "3": "小班", "4": "中班", "5": "大班", "6": "一年级", "7": "二年级"}
        # 提取 areaName, stageSort, ageTag, age, coreAge 和 title
        area_data = self.page_data.get('data', {}).get('areaData', [])
        for area in area_data:
            area_name = area.get('areaName', '')  # 获取 areaName

            # 获取 区域排序
            area_sort = area.get('style', '').get('fieldData', '').get('stageSort', '')
            stage_sort = ""
            for s in area_sort:
                stage_sort = stage_sort + class_id[s['stageAge']] + "：" + s['sortIndex'] + "\n"
            area_tabs = area.get('areaTab', [])

            for tab in area_tabs:
                title = tab['areaTabName']
                is_pay = tab['data'][0]['fieldData'].get('isPay', True) if tab['data'] else True  # 是否是付费子包
                is_free = f"\n(试玩{tab['data'][0]['fieldData'].get('freeStage', 0)}关)" if not is_pay else ""  # 获取免费子包试玩关卡

                package_ident = tab['data'][0]['fieldData']['packageIdent'] if tab['data'] else ""  # 子包的唯一标识，取首个分包的唯一标识
                total_stage = sum(int(item["fieldData"].get("totalStage", 0)) for item in tab['data'])  # 总关卡数

                age_tag = tab['style']['fieldData'].get('ageTag', '')
                age = tab['style']['fieldData'].get('age', '')
                core_age = tab['style']['fieldData'].get('coreAge', '')

                # 拼接成二维数组，顺序为 areaName, stage_sort, title, ageTag, age, coreAge
                row = [area_name, stage_sort, title + is_free, package_ident, total_stage, age_tag, age, core_age]
                result = np.append(result, [row], axis=0)
        return result


# 校验子包信息
class CheckPackageData:
    def __init__(self, package_data):
        self.package_data = package_data

    def is_exist_FileInfo(self, return_array=True):
        """
        判断子包文件和语言包文件是否存在
        :param return_array: 是否返回数组类型，True-返回数组类型，False-返回字典类型
        :return:
            result_arr: 子包信息校验结果（一个n行4列数组）
                数组包含字段：[package_ident, title, package_file_info, lang_file_info]
                            package_ident：子包标识
                            title：标题
                            package_file_info：子包文件Md5，子包文件不存在时填充“子包文件不存在”
                            lang_file_info：语言包文件Md5，语言包文件不存在时填充“语言包文件不存在”
            result_dict: 子包信息校验结果（字典类型）,key是子包标识，value包含参数title、package_file_info和lang_file_info
                字典格式示例：
                {
                    "math_1andmany": {
                                        "title": "One and Many",
                                        "package_file_info": "6bd009f375458ef00d13c2589791470a",
                                        "lang_file_info": "c508affb38e960f746415d85ce39687b"
                                    }
                }

        """
        package_data = self.package_data
        # 获取 packageDataList 数组
        package_data_list = package_data.get('data', {}).get('packageDataList', [])

        result_arr = np.empty((0, 4))

        result_dict = {}

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

            row = [package_ident, title, package_file_info, lang_file_info]
            result_arr = np.append(result_arr, [row], axis=0)

            result_dict[package_ident] = {
                'title': title,
                'package_file_info': package_file_info,
                'lang_file_info': lang_file_info
            }
        if return_array:
            return result_arr
        else:
            return result_dict


class SubPackageData:
    def __init__(self, subpackage_page_data):
        self.subpackage_page_data = subpackage_page_data

    def extr_subpackage_info(self):
        """
        从分包页面数据中提取分包信息
        :param subpackage_page_data: 分包页面数据
        :return subpackage_info: 分包信息列表
        """
        subpackage_page_data = self.subpackage_page_data
        # 检查ResultCode
        if subpackage_page_data.get("ResultCode") != "0":
            return None

        subpackage_info = []
        # 遍历每一个分包数据项
        for item in subpackage_page_data["Data"]["Data"]:
            languages = []  # 用于存储语言信息
            # 使用BeautifulSoup解析分包项中的语言数据
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(item.get("LangsData"), 'html.parser')

            # 提取语言名称和语言值，分别存储在对应的列表中
            spans_lang_name = soup.find_all("span", class_="el-tag--success")  # 找到所有语言名称的<span>
            spans_lang_value = soup.find_all("span", style="color:#409eff ")  # 找到所有语言值的<span>

            # 将语言名称和语言值逐一配对并添加到languages列表中
            for lang_name_span, lang_value_span in zip(spans_lang_name, spans_lang_value):
                lang_name = lang_name_span.get_text(strip=True)  # 提取语言名称并去掉多余空白
                lang_value = lang_value_span.get_text(strip=True)  # 提取语言值并去掉多余空白
                # 将语言信息以字典形式存储
                languages.append({
                    "lang_name": lang_name,
                    "lang_value": lang_value
                })

            # 将提取的分包信息添加到subpackage_info列表中
            subpackage_info.append({
                "SubPackageID": item.get("SubPackageID"),  # 分包ID
                "SubPackageName": item.get("SubPackageName"),  # 分包名称
                "SubPackageScence": item.get("SubPackageScence"),  # 分包场景
                "ConfigData": item.get("ConfigData"),  # 配置数据
                "SubPackageLangs": item.get("SubPackageLangs"),  # 分包语言
                "LangsData": languages,  # 语言数据
            })
        return subpackage_info


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


def get_all_lang_packagedatda(idents, platform, version, environment, country):
    """
    获取13国语言下x2、x4资源子包信息
    :param idents:子包标识列表
    :param platform:平台
    :param version:版本号
    :param environment:环境
    :param country:国家
    :return:
    """
    result_arr = np.empty((0, 6))

    for lang in header_config["language"]:
        data_request = DataRequester(platform, version, lang, environment, country)
        # 获取x2资源
        resource_type_code = "x2"
        body_x2 = data_request.make_packagedata_body(idents)
        fileInfo_x2 = CheckPackageData(data_request.packagedata(body_x2)).is_exist_FileInfo()
        if fileInfo_x2.size == 0:
            # 请求结果为空时，填充值
            first_col = np.array(idents).reshape(-1, 1)
            fill_cols = np.full((len(idents), 3), "无")
            fileInfo_x2 = np.hstack((first_col, fill_cols))
        result_x2 = np.insert(fileInfo_x2, (1, 1), (resource_type_code, lang), axis=1)

        # 获取x4资源
        resource_type_code = "x4"
        body_x4 = data_request.make_packagedata_body(idents, resource_type_code="x4")
        fileInfo_x4 = CheckPackageData(data_request.packagedata(body_x4)).is_exist_FileInfo()
        if fileInfo_x4.size == 0:
            first_col = np.array(idents).reshape(-1, 1)
            fill_cols = np.full((len(idents), 3), "无")
            fileInfo_x4 = np.hstack((first_col, fill_cols))
        result_x4 = np.insert(fileInfo_x4, (1, 1), (resource_type_code, lang), axis=1)
        # 合并数据
        result = np.vstack((result_x2, result_x4))
        result_arr = np.vstack((result_arr, result))
    # 排序
    indices = np.lexsort((result_arr[:, 1], result_arr[:, 0]))
    result_arr = result_arr[indices]

    return result_arr

# if __name__ == "__main__":
#     # 代码调试
#     args_ = args_common["思维正式"]["谷歌-英语"]
#     data_requester = DataRequester(args_["platform"], "2110120", args_["language"], args_["environment"],
#                                    args_["country"])
#     # body = data_requester.make_packagedata_body(["math_1andmany"], resource_type_code="X2")
#     # package_data = data_requester.packagedata(body)
#     package_data = data_requester.page_data("脑力开发")
#     print(package_data)
# idents = get_PackageIdent_By_Pagedata(DataRequester("安卓", "2050101", "简体", "正式线", "中国大陆").page_data_main())
# body = make_packagedata_body(idents)
# DataRequester("安卓", "2050101", "简体", "正式线", "中国大陆").packagedata(body)
# print(DataRequester("安卓", "2050101", "简体", "正式线", "中国大陆").packagedata(body_config["子包信息"]["加减"]))
