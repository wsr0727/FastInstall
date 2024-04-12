import os
import time
import logging
import zipfile
import shutil
import random
import json
from copy import deepcopy

"""
默认数据校验，相关方法
"""

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')


class DefaultCheck:
    def __init__(self, file_path):
        self.file_path = file_path

    lang_path = ['math_config_ar.json', 'math_config_en.json', 'math_config_es.json', 'math_config_fr.json',
                 'math_config_id.json', 'math_config_ja.json', 'math_config_ko.json', 'math_config_pt.json',
                 'math_config_ru.json', 'math_config_th.json', 'math_config_vi.json', 'math_config_zht.json']

    expand_lang_path = ['math_config_expand_ar.json', 'math_config_expand_en.json', 'math_config_expand_es.json',
                        'math_config_expand_fr.json', 'math_config_expand_id.json', 'math_config_expand_ja.json',
                        'math_config_expand_ko.json', 'math_config_expand_pt.json', 'math_config_expand_ru.json',
                        'math_config_expand_th.json', 'math_config_expand_vi.json', 'math_config_expand_zht.json']

    path_config = {
        "apk": {"image_path": "/assets/package_config/images/", "package_config_path": "/assets/package_config/",
                "package_config_expand_path": "/assets/package_config/",
                "default_game_path": "/assets/res/subModules/default_game.json"},
        "ipa": {"image_path": "/Payload/2d_noSuper_education.app/Images",
                "package_config_path": "/Payload/2d_noSuper_education.app/PackageConfig/",
                "package_config_expand_path": "/Payload/2d_noSuper_education.app/PackageConfig/",
                "default_game_path": "/Payload/2d_noSuper_education.app/res/subModules/default_game.json"},
        "aab": {"image_path": "/base/assets/package_config/images/",
                "package_config_path": "/base/assets/package_config/",
                "package_config_expand_path": "/base/assets/package_config/",
                "default_game_path": "/base/assets/res/subModules/default_game.json"}}
    # 解压目录，保存在相对路径
    path_cache = "/zip_cache_" + str(int(time.time()))

    def file_format(self):
        """判断文件格式"""
        file_format = [".apk", ".ipa", ".aab"]
        for f in file_format:
            if self.file_path.endswith(f):
                return f.replace(".", "")
        return False

    def zip_file(self):
        """解压文件"""
        # 创建 ZipFile 实例对象
        zip_file = zipfile.ZipFile(self.file_path)
        # 创建目录
        os.mkdir(self.path_cache)
        # 提取 zip 文件
        try:
            zip_file.extractall(self.path_cache)
            # 解压resources.arsc文件时会出错，只有打包出来的文件有问题，暂时没有解决办法
        except:
            pass
        # 关闭 zip 文件
        zip_file.close()

    def extract_json_data(self, path):
        """读取文件数据"""
        if self.file_exists(self.path_cache + path):  # 先判断文件存在且不为空
            with open(self.path_cache + path, "r", encoding="utf-8") as default_file:
                data = json.load(default_file)
            return data
        else:
            return {}

    @staticmethod
    def count_files(dir_path: str, extension: str):
        """判断文件夹内某个后缀的文件有多少个"""
        if os.path.isdir(dir_path):
            files = os.listdir(dir_path)
            count_files = [file for file in files if file.endswith('.' + extension)]
            logging.debug(str(files) + "文件内文件数量：" + extension + "：" + str(len(count_files)))
            return len(count_files)
        else:
            logging.debug("文件目录不存在")
            return -1

    @staticmethod
    def file_exists(file_path: str):
        """判断文件存在并且不为空"""
        return os.path.exists(file_path) and os.stat(file_path).st_size > 0

    def course_check(self):
        path_config = {
            "apk": {"default_game_path": "/assets/subapp_u2d/default_game.json"}
        }
        result = {"总状态": {"state": -1, "data": 0, "message": "失败"},
                  "内置子包": {"state": -1, "message": "【内置子包文件不存在】", "data": []}
                  }
        logging.debug("判断文件格式")
        file_format = self.file_format()
        if not file_format:
            result["总状态"]["message"] = "文件格式错误"
            return result

        logging.debug("解压文件")
        self.zip_file()
        default_game_md5_path = path_config[file_format]["default_game_path"]  # 默认子包
        default_game_md5_data = self.extract_json_data(default_game_md5_path)
        if default_game_md5_data:
            result["内置子包"].update({"state": 0, "message": "", "data": default_game_md5_data["item"]})
        state, message = DateCheck().final_result(result)
        result["总状态"].update({"state": state, "message": message})

        logging.debug("删除解压文件缓存")
        shutil.rmtree(self.path_cache)  # 删除解压后的文件
        logging.debug(json.dumps(result))
        return result

    def main(self):
        # state：-1 失败，0 成功。 message: 文件默认不存在
        result = {"总状态":
                      {"state": -1, "data": 0, "message": "失败"},
                  "内置子包":
                      {"state": -1, "message": "【内置子包文件不存在】", "data": []},
                  "内置图片":
                      {"state": -1, "message": "【内置图片文件夹不存在】", "data": []},
                  "首页数据（简体中文）":
                      {"state": -1, "message": "【简体中文首页数据文件不存在】", "data": []},
                  "首页数据（国际化语言）":
                      {"state": -1, "message": "【国际化语言首页数据文件不存在】", "file_count": 0, "random_file": "",
                       "data": []},
                  "趣味拓展数据（简体中文）":
                      {"state": -1, "message": "【趣味拓展中文文件不存在】", "file_count": 0, "random_file": "",
                       "data": []},
                  "趣味拓展数据（国际化语言）":
                      {"state": -1, "message": "【国际化语言趣味拓展文件不存在】", "file_count": 0, "random_file": "",
                       "data": []}}

        logging.debug("判断文件格式")
        file_format = self.file_format()
        if not file_format:
            result["总状态"]["message"] = "文件格式错误"
            return result

        logging.debug("解压文件")
        self.zip_file()

        # 组合需要的文件地址
        package_config_zh_path = self.path_config[file_format][
                                     "package_config_path"] + 'math_config_zh.json'  # 首页数据-中文
        package_config_lang_path = self.path_config[file_format][
                                       "package_config_path"] + random.choice(self.lang_path)  # 首页数据-多语言
        package_config_expand_zh_path = self.path_config[file_format][
                                            "package_config_expand_path"] + 'math_config_expand_zh.json'  # 趣味拓展-中文
        package_config_expand_lang_path = self.path_config[file_format][
                                              "package_config_expand_path"] + random.choice(
            self.expand_lang_path)  # 趣味拓展-多语言
        default_game_md5_path = self.path_config[file_format]["default_game_path"]  # 默认子包

        logging.debug("提取文件数据")
        package_config_zh_data = self.extract_json_data(package_config_zh_path)
        package_config_lang_data = self.extract_json_data(package_config_lang_path)
        package_config_expand_zh_data = self.extract_json_data(package_config_expand_zh_path)
        package_config_expand_lang_data = self.extract_json_data(package_config_expand_lang_path)
        default_game_md5_data = self.extract_json_data(default_game_md5_path)

        image_path_path = self.path_config[file_format]["image_path"]  # 默认1和许多卡片
        if file_format != "aab" and self.file_exists(self.path_cache + image_path_path):
            # 谷歌包不判断默认数据是否存在
            logging.debug("判断图片文件是否存在")
            image_png = self.count_files(self.path_cache + image_path_path, "png")  # 判断默认图片是否存在
            mp3_count = self.count_files(self.path_cache + image_path_path, "mp3")
            i_m_list = os.listdir(self.path_cache + image_path_path) if os.listdir(
                self.path_cache + image_path_path) else []
            if image_png >= 0 and mp3_count >= 0:
                result["内置图片"].update(
                    {"data": [{"图片数量": image_png, "音频数量": mp3_count, "文件列表": i_m_list}], "state": 0,
                     "message": ""})
            elif image_png == -1 or mp3_count == -1:
                result["内置图片"].update(
                    {"data": [{"图片数量": image_png, "音频数量": mp3_count, "文件列表": i_m_list}], "state": -1,
                     "message": "【音频或内置图片不存在】"})

        if package_config_zh_data:  # 首页数据-中文
            package_config_zh_result = DateCheck().package_config_check(package_config_zh_data)
            state, message = DateCheck().result_state(package_config_zh_result)
            result["首页数据（简体中文）"].update(
                {"data": package_config_zh_result, "state": state, "message": message})

        if file_format == "apk":  # 首页数据-多语言
            result["首页数据（国际化语言）"].update({"state": 0, "message": "【apk不判断海外(首页数据-多语言）文件】"})
        elif package_config_lang_data:  # 首页数据-多语言
            package_config_lang_result = DateCheck().package_config_check(package_config_lang_data, is_lang=True)
            file_count = self.count_files(self.path_cache + self.path_config[file_format]["package_config_path"],
                                          "json")
            result["首页数据（国际化语言）"].update(
                {"file_count": file_count, "random_file": package_config_lang_path.split("/")[-1],
                 "data": package_config_lang_result})
            state, message = DateCheck().result_state(package_config_lang_result)
            result["首页数据（国际化语言）"].update({"state": state, "message": message})

        if package_config_expand_zh_data:  # 趣味拓展-中文
            package_config_expand_zh_result = DateCheck().expand_config_check(package_config_expand_zh_data)
            state, message = DateCheck().expand_result_state(package_config_expand_zh_result)
            result["趣味拓展数据（简体中文）"].update(
                {"data": package_config_expand_zh_result, "state": state, "message": message})

        if file_format == "apk":  # 趣味拓展-多语言
            result["趣味拓展数据（国际化语言）"].update({"state": 0, "message": "【apk不判断海外（趣味拓展-多语言）文件】"})
        elif package_config_expand_lang_data:  # 趣味拓展-多语言
            file_count = self.count_files(
                self.path_cache + self.path_config[file_format]["package_config_expand_path"], "json")
            package_config_expand_lang_result = DateCheck().expand_config_check(package_config_expand_lang_data)
            state, message = DateCheck().expand_result_state(package_config_expand_lang_result)
            result["趣味拓展数据（国际化语言）"].update(
                {"file_count": file_count, "random_file": package_config_expand_lang_path.split("/")[-1],
                 "data": package_config_expand_lang_result, "state": state, "message": message})

        if default_game_md5_data:
            result["内置子包"].update({"state": 0, "message": "", "data": default_game_md5_data["item"]})
        logging.debug("编辑结果")
        state, message = DateCheck().final_result(result)
        result["总状态"].update({"state": state, "message": message})

        logging.debug("删除解压文件缓存")
        shutil.rmtree(self.path_cache)  # 删除解压后的文件
        logging.debug(json.dumps(result))
        return result


class DateCheck:
    @staticmethod
    def package_config_check(data, is_lang=False):
        """判断默认数据是否正常"""
        package_config_check_result = []
        level_result = {"level": "", "count": 0, "error": []}
        for level in data["areaData"]:
            level_result_copy = deepcopy(level_result)
            level_result_copy["level"] = level["style"]["fieldData"]["level"]
            for lesson in level["data"]:
                level_result_copy["count"] += 1
                if is_lang and lesson["dataCode"] != "ConfigData":
                    if any(t["type"] == "mv" for t in lesson["fieldData"]["stepConfig"]):
                        level_result_copy["error"].append(
                            {"areaDataID": lesson["areaDataID"], "id": lesson["id"], "title": lesson["title"],
                             "packageIdent": lesson["fieldData"]["packageIdent"],
                             "lang": lesson["fieldData"]["lang"]})
            package_config_check_result.append(level_result_copy)

        return list(package_config_check_result)

    @staticmethod
    def result_state(result):
        message = ""
        check = 0
        for l in result:
            if l["count"] <= 0:
                check -= 1
                message += "【level" + l["level"] + "没有课程】"

            if l["error"]:
                check -= 1
                message += "【level" + l["level"] + "国际化下存在MV环节】"
        if len(result) <= 3:
            check -= 1
            message += "【只有" + str(len(result)) + "个level，检查数量】"
        state = -1 if check < 0 else 0
        return state, message

    @staticmethod
    def expand_result_state(result):
        # 趣味拓展不再判断是否有免费课程,只判断课程总数是否大于0
        message = ""
        count = result[0]["count"]
        check = 0
        for i in result[0]["data"]:
            if i.get("无总关卡环节"):
                check -= 1
                message += "【趣味拓展存在无总关卡环节】"
                break
        if count <= 0:
            message += "【趣味拓展没有配置课程】"
            check -= 1
        # else:
        #     message += "【趣味拓展总课程数量：" + str(count) + "】"
        state = -1 if check < 0 else 0
        return state, message

    @staticmethod
    def final_result(result):
        state_all = 0
        message = ""
        for s in result.keys():
            if not s == "总状态":
                state_all = state_all + result[s]["state"]
                message = message + result[s]["message"]
        state = -1 if state_all < 0 else 0
        return state, message

    @staticmethod
    def expand_config_check(data):
        count = []
        hot_num = 0
        count_int = 0
        for d in data["areaData"]:
            count.append({"区域名": d["areaName"], "课程数据": {}})
            hot_tab = []
            total_stage_error = {}
            for i in d["areaTab"]:
                total_stage_empty = []
                count[-1]["课程数据"].update({i["areaTabName"]: len(i["data"])})
                for s in i["data"]:
                    if s["fieldData"].get("totalStage") in {"0", None}:
                        total_stage_empty.append(str(s["areaDataID"]) + ":" + s["title"])

                if i["style"]["fieldData"].get("isHot"):
                    hot_tab.append(i["areaTabName"])
                    hot_num += 1

                if total_stage_empty:
                    total_stage_error.update({i["areaTabName"]: total_stage_empty})
            if hot_tab:
                count[-1].update({"热门tab": hot_tab})
            if total_stage_error:
                count[-1].update({"无总关卡环节": total_stage_error})

        for j in count:
            for n in j["课程数据"].values():
                count_int = count_int + n

        package_config_expand_zh_result = [
            {"level": "趣味拓展", "count": count_int, "热门tab总数": hot_num, "data": count}]
        return package_config_expand_zh_result
