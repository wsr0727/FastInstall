import os
import time
import logging
import zipfile
import shutil
from tkinter import *
import windnd
import tkinter.scrolledtext as ScrolledText
import threading
import random
import json
from copy import deepcopy
import configparser
from tkinter import ttk
import requests

# 日志设置
# logging.basicConfig(filename='test.log', level=logging.DEBUG,
#                     format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')
# 打包指令 pyinstaller -F -w FastInstall.py
'''
快速安卓启动卸载
'''
devices = []  # 当前连接设备
task_list = []  # 任务列表


def config_set(key_value):
    # key_value = {"key": {"app_key": "value"}} 参数格式
    # 初始化设置文件

    # 创建一个解析器对象
    cfg = configparser.ConfigParser()
    if not os.path.exists("FastInstall.config"):
        # 如果没有，创建一个新文件
        with open("FastInstall.config", "w") as f:
            # 向设置文件写入默认内容
            f.write("[app]" + "\n")
            f.write("app_key = com.sinyee.babybus.mathIII" + "\n")
            f.write("app_key_histroy = []" + "\n")
            f.write("[cache]" + "\n")
            f.write("input_histroy = []" + "\n")

    # 读取config文件的内容
    cfg.read("FastInstall.config")

    logging.debug("设置默认值：" + str(key_value))
    for i in key_value.keys():
        for j in key_value[i]:
            cfg.set(i, j, str(key_value[i][j]))

    # 保存修改
    with open("FastInstall.config", "w") as f:
        cfg.write(f)
        logging.debug("保存默认文件的修改")


def cache_set():
    # 初始化缓存数据
    if os.path.exists("FastInstall.config"):
        cfg = configparser.ConfigParser()
        cfg.read("FastInstall.config")
        app_key_get = cfg.get("app", "app_key")
        if not cfg.has_option("app", "app_key_histroy"):
            cfg["app"] = {"app_key": app_key_get, "app_key_histroy": []}
            with open("FastInstall.config", "w") as configfile:
                cfg.write(configfile)
        app_key_histroy_get = cfg.get("app", "app_key_histroy")
        if not cfg.has_option("cache", "input_histroy"):
            cfg.add_section("cache")
            cfg["cache"] = {"input_histroy": []}
            with open("FastInstall.config", "w") as configfile:
                cfg.write(configfile)
        input_list_get = cfg.get("cache", "input_histroy") if cfg.get("cache", "input_histroy") else "[]"
        return app_key_get, eval(input_list_get), eval(app_key_histroy_get)
    else:
        # app_key 默认为"com.sinyee.babybus.mathIII",app_key_histroy默认为[]，input_list默认为[]
        return "com.sinyee.babybus.mathIII", [], []


app_key, input_list, app_key_histroy = cache_set()  # 初始化缓存


class TaskListObserver:
    """
    用于观测任务列表是否有变化，有变化时通知所有位置更新
    """

    def __init__(self):
        self._observers = []

    def register(self, observer):
        self._observers.append(observer)

    def notify(self):
        for observer in self._observers:
            observer()


task_list_observer = TaskListObserver()


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
        "apk": {"package_config_path": "/assets/package_config/",
                "package_config_expand_path": "/assets/package_config/",
                "default_game_path": "/assets/res/subModules/default_game.json"},
        "ipa": {"package_config_path": "/Payload/2d_noSuper_education.app/PackageConfig/",
                "package_config_expand_path": "/Payload/2d_noSuper_education.app/PackageConfig/",
                "default_game_path": "/Payload/2d_noSuper_education.app/res/subModules/default_game.json"},
        "aab": {"package_config_path": "/base/assets/package_config/",
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
        if count <= 0:
            message += "【趣味拓展没有配置课程】"
            state = -1
        else:
            message += "【趣味拓展总课程数量：" + str(count) + "】"
            state = 0
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
    def expand_count(data):
        if not data["areaData"]:
            return 0
        count = []
        count_int = 0
        hot_num = 0
        for d in data["areaData"]:
            count.append({"区域名": d["areaName"], "课程数据": {}})
            hot_tab = []
            for i in d["areaTab"]:
                count[-1]["课程数据"].update({i["style"]["headerTitle"]: len(i["data"])})
                try:
                    if i["style"]["fieldData"]["isHot"]:
                        hot_tab.append(i["style"]["headerTitle"])
                        hot_num += 1
                except:
                    pass
            if hot_tab:
                count[-1].update({"热门tab": hot_tab})

        for j in count:
            for n in j["课程数据"].values():
                count_int = count_int + n
        return count, count_int, hot_num

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
        state, message = self.final_result(result)
        result["总状态"].update({"state": state, "message": message})

        logging.debug("删除解压文件缓存")
        shutil.rmtree(self.path_cache)  # 删除解压后的文件
        logging.debug(json.dumps(result))
        return result

    def main(self):
        # state：-1 失败，0 成功。文件默认不存在
        result = {"总状态": {"state": -1, "data": 0, "message": "失败"},
                  "内置子包": {"state": -1, "message": "【内置子包文件不存在】", "data": []},
                  "首页数据（简体中文）": {"state": -1, "message": "【简体中文首页数据文件不存在】", "data": []},
                  "首页数据（国际化语言）": {"state": -1, "message": "【国际化语言首页数据文件不存在】", "file_count": 0, "random_file": "",
                                  "data": []},
                  "趣味拓展数据（简体中文）": {"state": -1, "message": "【趣味拓展中文文件不存在】", "file_count": 0,
                                   "random_file": "", "data": []},
                  "趣味拓展数据（国际化语言）": {"state": -1, "message": "【国际化语言趣味拓展文件不存在】", "file_count": 0,
                                    "random_file": "", "data": []}}

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

        if package_config_zh_data:  # 首页数据-中文
            package_config_zh_result = self.package_config_check(package_config_zh_data)
            state, message = self.result_state(package_config_zh_result)
            result["首页数据（简体中文）"].update(
                {"data": package_config_zh_result, "state": state, "message": message})

        if file_format == "apk":  # 首页数据-多语言
            result["首页数据（国际化语言）"].update({"state": 0, "message": "【apk不判断海外(首页数据-多语言）文件】"})
        elif package_config_lang_data:  # 首页数据-多语言
            package_config_lang_result = self.package_config_check(package_config_lang_data, is_lang=True)
            file_count = self.count_files(self.path_cache + self.path_config[file_format]["package_config_path"],
                                          "json")
            result["首页数据（国际化语言）"].update(
                {"file_count": file_count, "random_file": package_config_lang_path.split("/")[-1],
                 "data": package_config_lang_result})
            state, message = self.result_state(package_config_lang_result)
            result["首页数据（国际化语言）"].update({"state": state, "message": message})

        if package_config_expand_zh_data:  # 趣味拓展-中文
            data, count, hot_num = self.expand_count(package_config_expand_zh_data)
            package_config_expand_zh_result = [
                {"level": "趣味拓展", "count": count, "热门tab总数": hot_num, "data": data}]
            state, message = self.expand_result_state(package_config_expand_zh_result)
            result["趣味拓展数据（简体中文）"].update(
                {"data": package_config_expand_zh_result, "state": state, "message": message})

        if file_format == "apk":  # 趣味拓展-多语言
            result["趣味拓展数据（国际化语言）"].update({"state": 0, "message": "【apk不判断海外（趣味拓展-多语言）文件】"})
        elif package_config_expand_lang_data:  # 趣味拓展-多语言
            package_config_expand_lang_result = [
                {"level": "趣味拓展", "count": self.expand_count(package_config_expand_lang_data)}]
            file_count = self.count_files(
                self.path_cache + self.path_config[file_format]["package_config_expand_path"], "json")
            result["趣味拓展数据（国际化语言）"].update(
                {"file_count": file_count, "random_file": package_config_expand_lang_path.split("/")[-1],
                 "data": package_config_expand_lang_result})
            state, message = self.expand_result_state(package_config_expand_lang_result)
            result["趣味拓展数据（国际化语言）"].update({"state": state, "message": message})

        if default_game_md5_data:
            result["内置子包"].update({"state": 0, "message": "", "data": default_game_md5_data["item"]})
        logging.debug("编辑结果")
        state, message = self.final_result(result)
        result["总状态"].update({"state": state, "message": message})

        logging.debug("删除解压文件缓存")
        shutil.rmtree(self.path_cache)  # 删除解压后的文件
        logging.debug(json.dumps(result))
        return result


# 获取devices数量和名称
def get_devices_all():
    global devices
    devices = []  # 每次都重置设备列表
    for dName_ in os.popen('adb devices -l'):
        if "List of devices attached" not in dName_:
            name_list = dName_.split()
            if "device" in name_list:  # 只加入成功连接的设备
                devices.append([name_list[0], name_list[3].strip("model:")])
    return devices


# 输入指定字符
def input_text(device, text):
    command = 'adb -s ' + device + ' shell input text ' + text
    os.popen(command).read()


# 安装app
def adb_install(device, adress):
    install_last = get_packages_list(device)
    log_info = '设备：' + str(device) + '； ' + '文件：' + adress
    logging.debug("【正在安装】:" + log_info)
    install_command = 'adb -s ' + str(device) + ' install ' + '"{}"'.format(str(adress))
    install_result_str = os.popen(str(install_command))
    install_result = install_result_str.buffer.read().decode(encoding='utf-8')
    time.sleep(1)
    if 'Success' in install_result:
        install_after = get_packages_list(device)
        install_appkey = set(install_last) ^ set(install_after)
        logging.info("【安装成功】:" + log_info)
        return list(install_appkey), True
    else:
        logging.error("【安装失败】: adb命令：" + install_command + "  原因:\n" + install_result)


def get_packages_list(device):
    # 获取当前设备安装的应用
    packages_list_command = os.popen("adb -s " + device + " shell pm list packages -3").readlines()
    packages_list = [packages.split(":")[-1].splitlines()[0] for packages in packages_list_command]
    return packages_list


def get_adress(adress):
    adress_list = []
    logging.debug("正在处理的目录：" + adress)
    if os.path.isdir(adress):
        for f in os.listdir(adress):
            # 只装apk
            if ".apk" in f or ".ipa" in f or ".aab" in f:
                adress_list.append('{}/{}'.format(adress, f))
    else:
        adress_list = [item for item in adress.split("\n") if ".apk" in item or ".ipa" in item or ".aab" in item]
    return adress_list


# 卸载手机上所有应用
def uninstall(device, package_name):
    uninstall_command = os.popen('adb -s ' + device + " uninstall " + package_name).read()
    log_info = '包名：' + package_name + '  设备：' + str(device)
    if 'Success' in uninstall_command[-9:]:
        logging.info("【删除成功】：" + log_info)
        return True
    else:
        logging.error("【删除失败】" + log_info + "\n原因:\n" + uninstall_command)
        return False


def luncher_app(device, package_name):
    # 启动应用
    logging.debug("【正在启动应用】：" + package_name)
    os.popen("adb -s " + device + " shell am start " + package_name + "/com.sinyee.babybus.SplashAct").read()
    time.sleep(2)

    # 点击政策，没有也会点 不管成功失败
    screen_size = os.popen("adb -s " + device + " shell wm size").read()
    y, x = screen_size.split(":")[-1].strip().split("x")
    click_y = str(int(int(y) / 2 + 365))
    click_x = str(int(int(x) / 2))  # 居中的位置
    os.popen("adb -s " + device + " shell input touchscreen tap " + click_x + " " + click_y).read()  # 同意政策
    time.sleep(1)
    click_y_2 = str(int(int(y) / 2 + 350))
    os.popen("adb -s " + device + " shell input touchscreen tap " + click_x + " " + click_y_2).read()  # 同意隐私弹框

    # 开场动画
    time.sleep(15)


def open_app(device, package_name):
    # 启动应用
    logging.debug("【正在启动应用】：" + package_name)
    os.popen("adb -s " + device + " shell am start " + package_name + "/com.sinyee.babybus.SplashAct").read()


def release_debug(device, close=False):
    if not close:
        logging.debug("【开启正式线调试指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybus.app all").read()
    else:
        logging.debug("【关闭正式线调试指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybus.app none.").read()


def clear_app(device, app_key):
    logging.debug("【清空应用缓存】：" + device)
    os.popen("adb -s " + device + " shell pm clear " + app_key).read()


def setting_debug(device):
    logging.debug("【开启语言设置】：" + device)
    os.popen("adb -s " + device + " shell am start -a android.settings.LOCALE_SETTINGS").read()


def task_clear():
    """
    清空任务列表
    """
    global task_list
    task_list.clear()
    task_list_observer.notify()  # 通知任务列表已更新


def get_app_key(path):
    # 根据文件获取包名
    file_name = path.split('\\')[-1]
    if "/" in file_name:
        file_name = file_name.split('/')[-1]
    file_name_str = file_name.split('-')
    for i in file_name_str:
        if "com." in i:
            return file_name, i


def task_control(path=None, device="", status="未开始", app_id=None, task_id=0, commend=None, log=None, file_name=None):
    """
    用于更新任务列表task_list数据。
    模板{"序号": 0, "状态": status, "设备": device, "设备ID": device, "文件": path, "操作": [],"app_id"：“”，“日志”：None}
    :param path:文件路径
    :param device: 设备ID
    :param status: 完成状态
    :param task_id: 任务ID
    :param app_id: 应用包名
    :param commend: 操作按钮
    :param log: 日志
    :return:返回任务ID
    """
    global task_list, devices
    device_name = [n[1] for n in devices if device in n]
    if path:  # 地址不为空才判断
        result = get_app_key(path)
        if result:
            file_name = result[0]
            app_id = result[1]
    if log:
        log = deepcopy(log)
    if task_id == 0:
        task_id = len(task_list) + 1
        task_list.insert(0, {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path, "操作": commend,
                             "文件名": file_name, "app_id": app_id, "日志": log})
    else:
        for i in range(len(task_list)):
            if task_list[i]["序号"] == task_id:
                task_list[i] = {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                                "文件名": file_name, "操作": commend, "app_id": app_id, "日志": log}
                break

    task_list_observer.notify()  # 通知任务列表已更新

    return task_id


class InstallApp:
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.init_window_name.title("安卓测试工具")
        self.width = 1000
        # self.height = 520
        self.height = 530  # 加上”更多“按钮的高度
        self.init_window_name.geometry(str(self.width) + 'x' + str(self.height) + '+15+30')
        windnd.hook_dropfiles(self.init_window_name, func=self.dragg)

        # 顶部区域==============================================================
        self.top_frame = Frame(self.init_window_name)
        self.top_frame.grid(row=0, column=0, columnspan=2)
        self.massage_label = Label(self.top_frame, text="提示区域", width=70, font="微软雅黑 15 bold")
        self.massage_label.grid(row=0, column=0, columnspan=2)

        # 左边-上边区域==============================================================
        self.install_frame = Frame(self.init_window_name)
        self.install_frame.grid(row=1, column=0, sticky="N", padx=5)

        # 模式选择区域-------------------------------------------------------------
        self.mode_frame = LabelFrame(self.install_frame, text="安装模式选择：", width=self.width / 2)
        self.mode_frame.grid(row=0, column=0, sticky="N", padx=5)
        self.mode_data = StringVar()
        self.mode_data.set("仅安装")
        mode_list = ["仅安装", "批量出包安装(自动)", "批量出包安装(手动)"]
        radiobutton_w = int(60 / len(mode_list))
        for m in range(len(mode_list)):
            Radiobutton(self.mode_frame, text=mode_list[m], variable=self.mode_data, value=mode_list[m], indicatoron=0,
                        width=radiobutton_w).grid(row=0, column=m, sticky="N")
        # 包名区域----------------------
        self.app_key_frame = LabelFrame(self.install_frame, text="包名：（支持打开网页）", width=self.width / 2)
        self.app_key_frame.grid(row=1, column=0)
        self.app_key_var = StringVar()
        self.app_key_var.set(app_key)
        self.app_key_entry = ttk.Combobox(self.app_key_frame, textvariable=self.app_key_var, width=42,
                                          values=app_key_histroy)
        self.app_key_entry.grid(row=0, column=0)
        self.app_key_entry.bind("<<ComboboxSelected>>", self.app_key_select)
        self.app_key_button = Button(self.app_key_frame, text="打开", width=8,
                                     command=lambda: self.devices_manager("open"))
        self.app_key_button.grid(row=0, column=1)
        self.app_key_button = Button(self.app_key_frame, text="设置", width=8,
                                     command=lambda: self.app_key_setting(self.app_key_entry.get()))
        self.app_key_button.grid(row=0, column=2)

        # 文件地址区域-------------------------------------------------------------
        self.file_path_frame = LabelFrame(self.install_frame, text="文件地址（将文件拖入窗口任意位置即可获取文件地址）：")
        self.file_path_frame.grid(row=2, column=0)
        self.file_app_button = Button(self.file_path_frame, text="识别包名并设置", width=15, command=self.file_to_app_key)
        self.file_app_button.grid(row=0, column=0, sticky="W")

        self.course_defaule_button = Button(self.file_path_frame, text="科学默认数据", width=10,
                                            command=lambda: self.thread_it(self.default_check, None, "course"))
        self.course_defaule_button.grid(row=0, column=0)

        # 核验思维默认数据
        self.defaule_check_button = Button(self.file_path_frame, text="核验思维默认数据", width=15,
                                           command=lambda: self.thread_it(self.default_check))
        self.defaule_check_button.grid(row=0, column=0, sticky="E")

        # 文本框
        self.file_path_text = Text(self.file_path_frame, width=64, height=5)
        self.file_path_text.grid(row=1, column=0)

        # 右边-上边区域==============================================================
        # 设备选择区域-------------------------------------------------------------
        self.devices_frame = LabelFrame(self.install_frame, text="设备选择：（不选默认所有）", width=66)
        self.devices_frame.grid(row=0, column=1, rowspan=2)
        # 设备复选框
        self.checkboxes = {}
        self.devices_button = []
        self.devices = []
        self.devices_checkbutton()
        # 设备刷新按钮
        self.refresh_button = Button(self.devices_frame, text="刷新", width=8, command=self.devices_checkbutton)
        self.refresh_button.grid(row=0, column=0, sticky="E", ipadx=1)

        # 按钮区域-------------------------------------------------------------
        self.button_frame = Frame(self.install_frame)
        self.button_frame.grid(row=2, column=1, padx=8)
        self.choose_app_frame = LabelFrame(self.button_frame, text="应用管理：")
        self.choose_app_frame.grid(row=0, column=0, sticky="N", ipady=2, padx=5)
        # 开始按钮
        self.delete_button = Button(self.choose_app_frame, text="卸载应用", width=15,
                                    command=lambda: self.thread_it(self.devices_manager, "delete"))
        self.delete_button.grid(row=0, column=0, pady=5)
        self.delete_button = Button(self.choose_app_frame, text="清空应用缓存", width=15,
                                    command=lambda: self.thread_it(self.devices_manager, "clear"))
        self.delete_button.grid(row=0, column=1, pady=5)
        self.install_button = Button(self.choose_app_frame, text="安装", width=18,
                                     command=lambda: self.thread_it(self.run))
        self.install_button.grid(row=0, column=2)

        self.choose_devices_frame = LabelFrame(self.button_frame, text="设备管理：")
        self.choose_devices_frame.grid(row=1, column=0, sticky="N")

        self.debug_button = Button(self.choose_devices_frame, text="开启调试模式", width=15,
                                   command=lambda: self.thread_it(self.devices_manager, "debug"))
        self.debug_button.grid(row=0, column=0, pady=1)

        self.debug_button = Button(self.choose_devices_frame, text="关闭调试模式", width=15,
                                   command=lambda: self.thread_it(self.devices_manager, "debug_close"))
        self.debug_button.grid(row=0, column=1, pady=1)

        self.setting_button = Button(self.choose_devices_frame, text="打开语言设置", width=15,
                                     command=lambda: self.thread_it(self.devices_manager, "setting"))
        self.setting_button.grid(row=0, column=2, pady=1)
        # 下方区域==============================================================
        self.log_frame = LabelFrame(self.init_window_name, text="任务列表：（默认选中第一个任务）(双击任务可复制文件地址)")
        self.log_frame.grid(row=2, column=0, columnspan=2, padx=10)

        self.log_button_frame = LabelFrame(self.log_frame, text="操作：")
        self.log_button_frame.grid(row=0, column=1, sticky="N")
        btn_w = 15  # 操作按钮区域宽度
        btn_h = 1  # 操作按钮区域高度
        # 清空按钮
        self.clear_button = Button(self.log_button_frame, text="清空任务列表", height=btn_h, width=btn_w,
                                   command=self.clear_tree)
        self.clear_button.grid(row=0, column=0)

        # 打开按钮
        self.open_button = Button(self.log_button_frame, text="打开", height=btn_h, width=btn_w,
                                  command=lambda: self.task_commend("open"))
        self.open_button.grid(row=1, column=0)

        # 克隆按钮
        self.open_button = Button(self.log_button_frame, text="克隆", height=btn_h, width=btn_w,
                                  command=lambda: self.task_commend("clone"))
        self.open_button.grid(row=2, column=0)

        # 日志按钮
        self.open_button = Button(self.log_button_frame, text="日志", height=btn_h, width=btn_w,
                                  command=lambda: self.task_commend("log"))
        self.open_button.grid(row=3, column=0)
        # 设置包名按钮
        self.open_button = Button(self.log_button_frame, text="设置包名", height=btn_h, width=btn_w,
                                  command=lambda: self.task_commend("set_app_key"))
        self.open_button.grid(row=4, column=0)
        # 继续按钮
        self.continue_button = Button(self.log_button_frame, text="批量任务继续进行", height=btn_h, width=btn_w,
                                      command=self.is_continue)
        self.isContinue = False
        # 取消按钮
        self.cancel_button = Button(self.log_button_frame, text="取消后续任务", height=btn_h, width=btn_w,
                                    command=self.is_cancel)
        self.isCancel = False
        # self.continue_button.grid(row=5, column=0)
        # self.cancel_button.grid(row=6, column=0)

        # 创建一个Treeview控件
        self.tree = ttk.Treeview(self.log_frame)

        # 定义列
        self.tree["columns"] = ("状态", "设备", "文件名", "包名")
        self.task_tree_header = {"状态": 100, "设备": 120, "文件名": 380, "包名": 200}
        self.tree.column("#0", width=50, minwidth=30)
        self.tree.heading("#0", text="序号")
        self.tree.tag_configure('成功', foreground='green')
        self.tree.tag_configure('失败', foreground='red')

        # 设置列，#0是特殊的列，它指的是列表的第一列，设置显示的表头名
        for key, value in self.task_tree_header.items():
            self.tree.column(key, width=value, minwidth=value, anchor="center")
            self.tree.heading(key, text=key)

        # 将Treeview控件添加到窗口中
        self.tree.grid(row=0, column=0)
        task_list_observer.register(self.add_tree)

        self.tree.bind("<Double-Button-1>", self.copy_to_clipboard)

        # 扩展区域==============================================================
        # 拓展入口开关
        self.expand_Label = Label(self.init_window_name, text="\\v/ 更多")
        self.expand_Label.config(foreground='blue', font=('微软雅黑', 10, 'underline'))
        self.expand_off_Label = Label(self.init_window_name, text="/^\\ 收起")
        self.expand_off_Label.config(foreground='blue', font=('微软雅黑', 10, 'underline'))
        self.expand_Label.grid(row=3, column=0, sticky="E", ipadx=10)
        self.expand_Label.bind("<Button-1>", self.expand_show)
        self.expand_off_Label.bind("<Button-1>", self.expand_close)

        # 拓展入口开关
        self.expand_frame = LabelFrame(self.init_window_name, text="指定设备上输入字符：")
        self.input_Label = Label(self.expand_frame, text="内容：")
        self.input_var = StringVar()
        self.input_entry = Entry(self.expand_frame, textvariable=self.input_var, width=40)
        self.input_button = Button(self.expand_frame, text="输入",
                                   command=lambda: self.thread_it(self.devices_manager, "input"))
        # 创建一个Treeview控件
        self.input_histroy = ttk.Treeview(self.expand_frame)
        self.input_histroy.config(height=4)
        self.input_histroy.column("#0", width=350, anchor="w")
        self.input_histroy.heading("#0", text="输入历史(只保存20条，双击可再次输入)")
        if input_list:
            for h in input_list:
                self.input_histroy.insert("", "end", text=h)
        self.input_histroy.bind("<Double-Button-1>", self.click_to_input)
        self.input_CaptchaNo_test = Button(self.expand_frame, text="测试线输入验证码", width=15,
                                           command=lambda: self.input_captcha_no("test"))
        self.input_CaptchaNo = Button(self.expand_frame, text="正式线输入验证码", width=15, command=self.input_captcha_no)
        self.input_CaptchaNo_label = Label(self.expand_frame, text="先选手机号再点")

    def file_to_app_key(self):
        file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
        if not file_path_data:  # 地址不为空才判断
            self.massage_label.config(text="文件地址为空")
            return
        result = get_app_key(file_path_data)
        if not result:
            self.massage_label.config(text="识别失败")
            return
        self.app_key_setting(result[1])

    # ========扩展区域
    def expand_show(self, event):
        self.height = 530 + 200
        self.init_window_name.geometry(str(self.width) + 'x' + str(self.height))
        self.expand_Label.grid_remove()
        self.expand_off_Label.grid(row=3, column=0, sticky="E", ipadx=10)

        self.expand_frame.grid(row=4, column=0, sticky="NW", padx=15)
        self.input_Label.grid(row=0, column=0)
        self.input_entry.grid(row=0, column=1)
        self.input_button.grid(row=0, column=2)
        self.input_histroy.grid(row=1, column=0, columnspan=4, pady=1)
        self.input_CaptchaNo_test.grid(row=2, column=0, columnspan=2, sticky="W")
        self.input_CaptchaNo.grid(row=2, column=1, ipadx=5)
        self.input_CaptchaNo_label.grid(row=2, column=1, columnspan=2, sticky="E", ipadx=2)

    def expand_close(self, event):
        self.height = 530
        self.init_window_name.geometry(str(self.width) + 'x' + str(self.height))
        self.expand_off_Label.grid_remove()
        self.expand_Label.grid(row=3, column=0, sticky="E", ipadx=10)

        self.expand_frame.grid_remove()
        self.input_Label.grid_remove()
        self.input_entry.grid_remove()
        self.input_button.grid_remove()
        self.input_histroy.grid_remove()
        self.input_CaptchaNo.grid_remove()

    def input_histroy_list(self, text=""):
        # 处理输入历史的列表
        global input_list
        if text in input_list:
            input_list.remove(text)
        else:
            self.input_histroy.insert("", 0, text=text)
        input_list.insert(0, text)

        if len(input_list) >= 20:
            input_list = input_list[:20]

        config_set({"cache": {"input_histroy": input_list}})

    def click_to_input(self, event):
        item = self.input_histroy.identify('item', event.x, event.y)
        if not item:
            return
        text = self.input_histroy.item(item)['text']
        self.devices_manager(name="input", text=text)

    def input_captcha_no(self, domain_name=""):
        # 输入验证码
        cur_item = self.input_histroy.focus()
        if not cur_item:
            return
        text = self.input_histroy.item(cur_item)['text']
        host = "https://udb.babybus.com" if not domain_name == "test" else "https://udb.development.platform.babybus.com"
        url = host + "/AppSync/GetPhoneCaptcha?Phone=" + text + "&AccountGroupID=1"

        try:
            response = requests.request("GET", url)
            res = json.loads(response.text)
        except:
            res = {"ResultCode": -1}

        if res["ResultCode"] == "0":
            self.devices_manager(name="input", text=res["Data"]['CaptchaNo'])
            self.input_CaptchaNo_label.config(text="已输入：" + res["Data"]['CaptchaNo'])
        else:
            self.input_CaptchaNo_label.config(text="失败" + text)

    # ===========任务列表使用的方法
    def copy_to_clipboard(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        task_id = self.tree.item(item)['text']
        path = self.get_task(task_id)["文件"]
        if path:
            self.init_window_name.clipboard_clear()
            self.init_window_name.clipboard_append(path)
            self.massage_label.config(text=f"已复制： {path} ")

    def add_tree(self):
        row_data = self.tree.get_children()
        # 取第一行的序号，没有的话就是0
        first_id = self.tree.item(row_data[0])["text"] if row_data else 0
        for i in task_list:
            # 只更新没有更新过的数据
            if i["序号"] > int(first_id):
                item_id = self.tree.insert("", 0, text=i["序号"], values=(i['状态'], i['设备'], i['文件名'], i['app_id']))
                i["item_id"] = item_id
            elif i["序号"] == int(first_id):
                # 如果当前需要已经写入过了，就跳出循环
                break

    def set_state_tree(self, item_id, new_value):
        # 更新状态，设置颜色
        self.tree.set(item_id, "状态", new_value)
        if "成功" in new_value:
            self.tree.item(item_id, tags=('成功',))
        elif "失败" in new_value:
            self.tree.item(item_id, tags=('失败',))

    def clear_tree(self):
        row_data = self.tree.get_children()
        if row_data:
            task_clear()
            for i in row_data:
                self.tree.delete(i)

    def get_cur_item(self):
        # 获取当前列表的选中项
        cur_item = self.tree.focus()
        if not cur_item:
            # 没有选中默认第一个
            top_items = self.tree.get_children()
            if top_items:
                top_item_id = top_items[0]
                return self.tree.item(top_item_id)
            self.massage_label.config(text="没有任务可选")
        else:
            return self.tree.item(cur_item)

    def task_commend(self, commend_tpye):
        # 任务列表的操作按钮
        cur_item = self.get_cur_item()
        if not cur_item:
            self.massage_label.config(text="没有已选择的任务")
            return
        task = self.get_task(cur_item['text'])  # 获取任务详情
        if commend_tpye == "open":
            self.devices_manager(name="open", task=task)
        elif commend_tpye == "clone":
            self.thread_it(self.clone_task, task)
        elif commend_tpye == "log":
            if task["日志"]:
                self.show_log(task)
            else:
                self.massage_label.config(text="日志为空")
        elif commend_tpye == "set_app_key":
            self.app_key_setting(new_app_key=task["app_id"])

    def app_key_select(self, eventObject):
        # 包名下拉框选择事件
        self.app_key_setting(self.app_key_entry.get())

    def app_key_setting(self, new_app_key):
        global app_key, app_key_histroy
        app_key = new_app_key
        self.app_key_var.set(app_key)
        config_set({"app": {"app_key": app_key}})

        if app_key in app_key_histroy:
            app_key_histroy.remove(app_key)

        app_key_histroy.insert(0, app_key)
        if len(app_key_histroy) >= 10:
            app_key_histroy = app_key_histroy[:10]
        self.app_key_entry['values'] = app_key_histroy

        config_set({"app": {"app_key_histroy": app_key_histroy}})
        self.massage_label.config(text="已设置包名" + app_key)

    @staticmethod
    def show_log(task):
        def state_str(state):
            if state == 0:
                return "成功"
            else:
                return "失败"

        def level_conunt_text(count):
            for i in count:
                log_text.insert("end", "阶段-" + i["level"] + "：课程数量 " + str(i["count"]) + "\n")
                if i["error"]:
                    log_text.insert("end", "海外存在MV环节的课程：" + str(i["error"]) + "\n")
                log_text.insert("end", "-" * 20 + "\n", "标题")

        def expand_conunt_text(count):
            log_text.insert("end", "热门tab总数:" + str(count[0]["热门tab总数"]) + "\n")
            log_text.insert("end", "-" * 20 + "\n", "标题")
            for i in count[0]["data"]:
                for key in i.keys():
                    log_text.insert("end", key + "：" + str(i[key]) + "\n")
                log_text.insert("end", "-" * 20 + "\n", "标题")

        log = task["日志"]
        # 创建一个新的Toplevel窗口
        log_top = Toplevel()
        log_top.title("核验默认数据结果")

        # 在窗口中创建一个文本框来显示日志内容
        log_text = Text(log_top, font="微软雅黑 10 bold")
        log_text.pack()
        # 设置文本和样式
        log_text.tag_configure("标题", foreground="blue")
        log_text.tag_configure("成功", foreground="green")
        log_text.tag_configure("失败", foreground="red")

        for title, content in log.items():
            log_text.insert("end", "========" + title + "========\n", "标题")
            for t, c in content.items():
                if t == "data" and c:
                    if "level" in c[0].keys() and c[0]["level"] == "趣味拓展":
                        expand_conunt_text(c)
                    else:
                        try:
                            level_conunt_text(c)
                        except KeyError:
                            log_text.insert("end", "数据" + "：" + str(c) + "\n")
                elif t == "state":
                    log_text.insert("end", "结果" + "：" + state_str(c) + "\n", state_str(c))
                elif t == "message":
                    log_text.insert("end", "信息：" + c + "\n")
                elif t == "file_count":
                    log_text.insert("end", "文件数量（首页+趣味）" + "：" + str(c) + "\n")
                elif t == "random_file" and c:
                    log_text.insert("end", "选取的国际化语言文件" + "：" + str(c) + "\n")

        log_text.configure(state="disabled")

    def clone_task(self, task):
        if '安装' in task['状态']:
            self.thread_it(self.run_install, task['文件'], [task['设备ID']])
        elif '卸载' in task['状态']:
            self.thread_it(self.devices_manager, "delete")
        elif '开启调试' in task['状态']:
            self.thread_it(release_debug, task['设备ID'])
            task_control(device=task['设备ID'], status="开启调试")
        elif '清空' in task['状态']:
            self.thread_it(clear_app, task['设备ID'], task['app_id'])
            task_control(app_id=task['app_id'], path=task['app_id'], device=task['设备ID'], status="清空")
        elif '核验' in task['状态']:
            self.default_check(task=task)
        else:
            self.massage_label.config(text="此任务不支持克隆")

    def devices_checkbutton(self):
        # 构建复选框
        while self.devices_button:
            check_btn = self.devices_button.pop()
            check_btn.destroy()
        self.checkboxes = {}
        self.devices = get_devices_all()
        if len(self.devices) == 0:
            c = Checkbutton(self.devices_frame, text="无设备连接", state='disabled', width=66)
            c.grid(row=1, column=0)
            self.devices_button.append(c)
        else:
            for i in range(len(self.devices)):
                self.checkboxes[i] = BooleanVar()
                c = Checkbutton(self.devices_frame, text=self.devices[i][1], variable=self.checkboxes[i],
                                width=int(66 / len(self.devices)))
                c.grid(row=1, column=i)
                self.devices_button.append(c)

    def devices_checkbutton_get(self):
        # 获取复选框选中数据，不选默认所有
        select_devices = []
        devices_all = []
        for i in self.checkboxes:
            if self.checkboxes[i].get():
                select_devices.append(self.devices[i][0])
            devices_all.append(self.devices[i][0])
        if not select_devices:
            select_devices = devices_all
        return select_devices

    def delete_task(self, device, app_id):
        # 卸载任务管理
        task_id = task_control(app_id=app_id, device=device, status="卸载中")
        result = uninstall(device, app_id)
        item_id = self.get_task(task_id)["item_id"]
        if result:
            task_control(task_id=task_id, app_id=app_id, device=device, status="卸载成功")
            self.set_state_tree(item_id, "卸载成功")
        else:
            task_control(task_id=task_id, app_id=app_id, device=device, status="卸载失败")
            self.set_state_tree(item_id, "卸载失败")

    def devices_manager(self, name, text="", task=None):
        # 需要使用到设备的方法，都先判断一遍是否有选中的设备
        select_devices = self.devices_checkbutton_get()
        if not select_devices:
            self.massage_label.config(text="没有选中设备")
            return

        if name == "open" and task:
            open_app(task['设备ID'], task['app_id'])
            return

        global app_key
        for d in select_devices:
            if name == "setting":
                self.thread_it(setting_debug, d)
                task_control(device=d, status="开启语言设置")
            elif name == "debug":
                self.thread_it(release_debug, d)
                task_control(device=d, status="开启调试")
            elif name == "debug_close":
                self.thread_it(release_debug, d, True)
                task_control(device=d, status="关闭调试")
            elif name == "clear":
                self.thread_it(clear_app, d, app_key)
                task_control(app_id=app_key, device=d, status="清空")
            elif name == "input":
                if not text:
                    self.thread_it(input_text, d, self.input_var.get())
                    self.input_histroy_list(text=self.input_var.get())
                else:
                    self.thread_it(input_text, d, text)
                    # self.input_histroy_list(text=text) # 写入缓存
            elif name == "delete":
                packages = get_packages_list(d)
                if app_key in packages:
                    self.thread_it(self.delete_task, d, app_key)
                else:
                    task_control(app_id=app_key, device=d, status="设备上无包")
            elif name == "open":
                open_app(d, self.app_key_entry.get())

    @staticmethod
    def get_task(task_id):
        # 获取任务详情
        for i in task_list:
            if i["序号"] == task_id:
                return i

    def default_check(self, task=None, app_name=""):
        if not task:
            file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
            file_list = get_adress(file_path_data)
        else:
            file_list = [task['文件']]

        if not file_list:
            self.massage_label.config(text="请输入文件地址")
            return

        for index, f in enumerate(file_list):
            task_id = task_control(path=f, status="核验包数据")
            self.massage_label.config(text="检测默认数据，第" + str(index + 1) + "个安装包")

            if app_name == "course":
                result = DefaultCheck(f).course_check()
            else:
                result = DefaultCheck(f).main()

            item_id = self.get_task(task_id)["item_id"]
            if result["总状态"]["state"] == 0:
                task_control(task_id=task_id, path=f, device="", status="核验包成功", log=result, commend=["日志"])
                self.set_state_tree(item_id, "核验包成功")
            elif result["总状态"]["state"] == -1:
                task_control(task_id=task_id, path=f, device="", status="核验包失败", log=result, commend=["日志"])
                self.set_state_tree(item_id, "核验包失败")
        self.massage_label.config(text="检测默认数据完成")

    def run_install(self, path, devices_list, appkey=None, is_luncher=False):
        # 卸载、安装、启动、点击协议
        for device in devices_list:
            task_id = task_control(path=path, device=device, status="安装进行中")
            if appkey:
                uninstall(device, appkey)
            appkey_list = adb_install(device, path)  # 安装,获取包名
            item_id = self.get_task(task_id)["item_id"]
            if appkey_list:
                task_control(path=path, device=device, status="安装成功", app_id=appkey_list[0], task_id=task_id,
                             commend=["打开"])
                self.set_state_tree(item_id, "安装成功")
                if is_luncher:
                    appkey = appkey_list[0][0]
                    luncher_app(device, appkey)
            else:
                task_control(path=path, device=device, status="安装失败", task_id=task_id, commend=[])
                self.set_state_tree(item_id, "安装失败")
        return appkey

    def run(self):
        file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
        if len(file_path_data) <= 0:
            self.massage_label.config(text="请填写正确文件路径")
        elif not self.devices:
            self.massage_label.config(text="当前没有连接的设备")
        else:
            select_devices = self.devices_checkbutton_get()
            file_list = get_adress(file_path_data)
            app_key_run = None
            for index, f in enumerate(file_list):
                if self.isCancel:
                    self.isCancel = False
                    break
                if self.mode_data.get() == "仅安装":
                    self.thread_it(self.run_install, f, select_devices)
                else:
                    self.massage_label.config(text="批量任务进行中：第" + str(index + 1) + "个安装包开始")
                    app_key_run = self.run_install(f, select_devices, app_key_run, True)
                    self.massage_label.config(text="批量任务进行中：第" + str(index + 1) + "个安装包结束")
                    if index != len(file_list) - 1 and self.mode_data.get() == "批量出包安装(手动)":
                        self.continue_button.grid(row=5, column=0)
                        self.cancel_button.grid(row=6, column=0)
                        while not self.isContinue:
                            if self.isCancel:
                                self.massage_label.config(text="批量任务取消")
                                break
                        self.continue_button.grid_remove()
                        self.cancel_button.grid_remove()
                        self.isContinue = False
                    elif index == len(file_list) - 1:
                        self.massage_label.config(text="批量任务结束")

    def is_continue(self):
        self.isContinue = True

    def is_cancel(self):
        self.isCancel = True

    @staticmethod
    def thread_it(func, *args):
        """将函数打包进线程"""
        # 创建
        t = threading.Thread(target=func, args=args)
        # 守护
        t.setDaemon(True)
        # 启动
        t.start()

    def dragg(self, files):
        msg = '\n'.join((item.decode("gbk") for item in files))
        self.file_path_text.delete("1.0", "end")
        self.file_path_text.insert("1.0", msg)


def gui_start():
    init_window = Tk()  # 实例化出一个父窗口
    InstallApp(init_window)
    init_window.mainloop()


if __name__ == '__main__':
    gui_start()
