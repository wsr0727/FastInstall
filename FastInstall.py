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

# 打包指令 pyinstaller -F -w FastInstall.py

'''
快速安卓启动卸载
'''
# 日志设置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')

devices = []  # 当前连接设备
task_list = []
app_key = "com.sinyee.babybus.mathIII"


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
    # state：-1 失败，0 成功。文件默认不存在
    result = {"state": -1,
              "message": "失败",
              "data": {"image": {"state": -1, "data": 0, "message": "【默认图片文件不存在】"},
                       "package_config_zh": {"state": -1, "message": "【简体中文首页数据文件不存在】", "data": []},
                       "package_config_lang": {"state": -1, "message": "【国际化语言首页数据文件不存在】", "file_count": 0,
                                               "random_file": "", "data": []},
                       "package_config_expand_zh": {"state": -1, "message": "【趣味拓展中文文件不存在】", "file_count": 0,
                                                    "random_file": "", "data": []},
                       "package_config_expand_lang": {"state": -1, "message": "【国际化语言趣味拓展文件不存在】", "file_count": 0,
                                                      "random_file": "", "data": []},
                       "default_game": {"state": -1, "message": "【内置子包文件不存在】", "data": []}}}

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
        zip_file.extractall(self.path_cache)
        # 关闭 zip 文件
        zip_file.close()

    def delete_file(self):
        """删除解压后的文件"""
        shutil.rmtree(self.path_cache)

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
            logging.debug("文件内文件数量：" + extension + "：" + str(len(count_files)))
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
        # grade=0，为体验岛没有选择阶段的课程
        level_0_result = {"level": "0", "count": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}, "error": []}
        level_result = {"level": "", "count": 0, "error": []}
        for level in data["areaData"]:
            if level["style"]["fieldData"]["level"] == "0":
                level_0_result_copy = deepcopy(level_0_result)
                for grade in level["data"]:
                    level_0_result_copy["count"][grade['fieldData']["grade"]] += 1
                    if is_lang:
                        if any(t["type"] == "mv" for t in grade["fieldData"]["stepConfig"]):
                            level_0_result_copy["error"].append(
                                {"areaDataID": grade["areaDataID"], "id": grade["id"], "title": grade["title"],
                                 "packageIdent": grade["fieldData"]["packageIdent"],
                                 "lang": grade["fieldData"]["lang"], "grade": grade["fieldData"]["grade"]})
                package_config_check_result.append(level_0_result_copy)
            else:
                level_result_copy = deepcopy(level_result)
                level_result_copy["level"] = level["style"]["fieldData"]["level"]
                for lesson in level["data"]:
                    level_result_copy["count"] += 1
                    if is_lang:
                        if any(t["type"] == "mv" for t in lesson["fieldData"]["stepConfig"]):
                            level_result_copy["error"].append(
                                {"areaDataID": lesson["areaDataID"], "id": lesson["id"], "title": lesson["title"],
                                 "packageIdent": lesson["fieldData"]["packageIdent"],
                                 "lang": lesson["fieldData"]["lang"]})
                package_config_check_result.append(level_result_copy)

        return list(package_config_check_result)

    @staticmethod
    def package_config_expand_check(data):
        """判断趣味拓展默认数据是否正常"""
        package_config_expand_check_result = []
        # grade=0，为体验岛没有选择阶段的课程
        expand_0_result = {"level": "趣味拓展-0", "count": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0},
                           "error": []}  # 免费课程每个阶段都需要有
        expand_result = {"level": "趣味拓展", "count": 0, "error": []}
        for expand in data["areaData"][0]["data"]:  # 只取第一个趣味拓展分类
            if "grade" in expand["fieldData"] and "priceInfo" in expand["fieldData"]:  # 是否有选阶段，是否有价格信息
                if expand["fieldData"]["priceInfo"]["priceType"] == 1:
                    expand_0_result["count"][expand['fieldData']["grade"]] += 1
            else:
                expand_result["count"] += 1
        package_config_expand_check_result.append(expand_0_result)
        package_config_expand_check_result.append(expand_result)
        return list(package_config_expand_check_result)

    @staticmethod
    def result_state(result):
        message = ""
        check = 0
        level_0 = -1  # 判断体验岛是否存在
        for l in result:
            if l["level"] == "0":
                level_0 += 1
                for key, value in l["count"].items():
                    if value == 0 and key != "0":
                        check -= 1
                        message += "【体验岛" + key + "阶段没有课程】"
            else:
                if l["count"] <= 0:
                    check -= 1
                    message += "【level" + l["level"] + "没有课程】"
            if l["error"]:
                check -= 1
                message += "【level" + l["level"] + "国际化下存在MV环节】"
        if level_0 == -1:
            check -= 1
            message += "【体验岛不存在】"
        if len(result) <= 3:
            check -= 1
            message += "【只有" + str(len(result)) + "个level，检查数量】"
        state = -1 if check < 0 else 0
        return state, message

    @staticmethod
    def expand_result_state(result):
        message = ""
        check = 0
        for level in result:
            if level["level"] == "趣味拓展-0":
                for key, value in level["count"].items():
                    if value == 0 and key != "0":
                        check -= 1
                        message += "【趣味拓展" + key + "阶段没有免费课程】"
            else:
                if level["count"] <= 0:
                    check -= 1
                    message += "【趣味拓展没有除免费课程外的课程】"
        state = -1 if check < 0 else 0
        return state, message

    @staticmethod
    def final_result(result):
        state_all = result["data"]["image"]["state"] + result["data"]["package_config_zh"]["state"] + \
                    result["data"]["package_config_lang"]["state"] + result["data"]["default_game"]["state"] + \
                    result["data"]["package_config_expand_zh"]["state"] + result["data"]["package_config_expand_lang"][
                        "state"]
        state = -1 if state_all < 0 else 0
        message = result["data"]["image"]["message"] + result["data"]["package_config_zh"]["message"] + \
                  result["data"]["package_config_lang"]["message"] + result["data"]["default_game"]["message"] + \
                  result["data"]["package_config_expand_zh"]["message"] + result["data"]["package_config_expand_lang"][
                      "message"]
        return state, message

    def main(self):
        logging.debug("判断文件格式")
        file_format = self.file_format()
        if not file_format:
            self.result["message"] = "文件格式错误"
            return self.result

        logging.debug("解压文件")
        self.zip_file()

        # 组合需要的文件地址
        image_path_path = self.path_config[file_format]["image_path"]  # 默认图片
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

        logging.debug("判断图片文件是否存在")
        image_png = self.count_files(self.path_cache + image_path_path, "png")  # 判断默认图片是否存在
        if image_png >= 0:
            self.result["data"]["image"].update({"data": image_png, "state": 0, "message": ""})

        logging.debug("提取文件数据")
        package_config_zh_data = self.extract_json_data(package_config_zh_path)
        package_config_lang_data = self.extract_json_data(package_config_lang_path)
        package_config_expand_zh_data = self.extract_json_data(package_config_expand_zh_path)
        package_config_expand_lang_data = self.extract_json_data(package_config_expand_lang_path)
        default_game_md5_data = self.extract_json_data(default_game_md5_path)

        if package_config_zh_data:  # 首页数据-中文
            package_config_zh_result = self.package_config_check(package_config_zh_data)
            state, message = self.result_state(package_config_zh_result)
            self.result["data"]["package_config_zh"].update(
                {"data": package_config_zh_result, "state": state, "message": message})

        if file_format == "apk":  # 首页数据-多语言
            self.result["data"]["package_config_lang"].update({"state": 0, "message": "【apk不判断海外(首页数据-多语言）文件】"})
        else:
            if package_config_lang_data:  # 首页数据-多语言
                package_config_lang_result = self.package_config_check(package_config_lang_data, is_lang=True)
                file_count = self.count_files(self.path_cache + self.path_config[file_format]["package_config_path"],
                                              "json")
                self.result["data"]["package_config_lang"].update(
                    {"file_count": file_count, "random_file": package_config_lang_path.split("/")[-1],
                     "data": package_config_lang_result})
                state, message = self.result_state(package_config_lang_result)
                self.result["data"]["package_config_lang"].update({"state": state, "message": message})

        if package_config_expand_zh_data:  # 趣味拓展-中文
            package_config_expand_zh_result = self.package_config_expand_check(package_config_expand_zh_data)
            state, message = self.expand_result_state(package_config_expand_zh_result)
            self.result["data"]["package_config_expand_zh"].update(
                {"data": package_config_expand_zh_result, "state": state, "message": message})

        if file_format == "apk":  # 趣味拓展-多语言
            self.result["data"]["package_config_expand_lang"].update({"state": 0, "message": "【apk不判断海外（趣味拓展-多语言）文件】"})
        else:
            if package_config_expand_lang_data:  # 趣味拓展-多语言
                package_config_expand_lang_result = self.package_config_expand_check(package_config_expand_lang_data)
                file_count = self.count_files(
                    self.path_cache + self.path_config[file_format]["package_config_expand_path"], "json")
                self.result["data"]["package_config_expand_lang"].update(
                    {"file_count": file_count, "random_file": package_config_expand_lang_path.split("/")[-1],
                     "data": package_config_expand_lang_result})
                state, message = self.expand_result_state(package_config_expand_lang_result)
                self.result["data"]["package_config_expand_lang"].update({"state": state, "message": message})

        if default_game_md5_data:
            self.result["data"]["default_game"].update(
                {"state": 0, "message": "", "data": default_game_md5_data["item"]})
        logging.debug("编辑结果")
        state, message = self.final_result(self.result)
        self.result.update({"state": state, "message": message})

        logging.debug("删除解压文件缓存")
        self.delete_file()
        logging.debug(json.dumps(self.result))
        return self.result


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
    time.sleep(1)


def open_app(device, package_name):
    # 启动应用
    logging.debug("【正在启动应用】：" + package_name)
    os.popen("adb -s " + device + " shell am start " + package_name + "/com.sinyee.babybus.SplashAct").read()


def release_debug(device):
    # 开启正式线调试指令
    logging.debug("【开启正式线调试指令】：" + device)
    os.popen("adb -s " + device + " shell setprop debug.babybus.app all").read()


def clear_app(device, app_key):
    # 开启正式线调试指令
    logging.debug("【清空应用缓存】：" + device)
    os.popen("adb -s " + device + " shell pm clear " + app_key).read()


def setting_debug(device):
    # 开启语言设置
    logging.debug("【开启语言设置】：" + device)
    os.popen("adb -s " + device + " shell am start -a android.settings.LOCALE_SETTINGS").read()


def run_install(path, devices_list, appkey=None, is_luncher=False):
    # 卸载、安装、启动、点击协议
    for device in devices_list:
        task_id = task_control(path, device, "安装进行中")
        if appkey:
            uninstall(device, appkey)
        appkey_list = adb_install(device, path)  # 安装,获取包名
        if appkey_list:
            task_control(path, device, "安装成功", appkey_list[0], task_id, commend=["打开"])
            if is_luncher:
                appkey = appkey_list[0][0]
                luncher_app(device, appkey)
        else:
            task_control(path, device, "安装失败", task_id=task_id, commend=[])
    return appkey


def task_clear():
    """
    # 清空任务列表
    """
    global task_list
    task_list.clear()
    task_list_observer.notify()  # 通知任务列表已更新


def task_control(path="", device="", status="未开始", app_id=None, task_id=0, commend=None, log=None):
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
    if task_id == 0:
        task_id = len(task_list) + 1
        task_list.insert(0, {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path, "操作": commend,
                             "app_id": app_id, "日志": log})
    else:
        for i in range(len(task_list)):
            if task_list[i]["序号"] == task_id:
                task_list[i] = {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                                "操作": commend, "app_id": app_id, "日志": log}

    task_list_observer.notify()  # 通知任务列表已更新
    return task_id


class InstallApp:
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.init_window_name.title("装包工具")
        self.width = 1020
        self.height = 520
        self.init_window_name.geometry(str(self.width) + 'x' + str(self.height) + '+15+30')
        windnd.hook_dropfiles(self.init_window_name, func=self.dragg)

        # 顶部区域==============================================================
        self.top_frame = Frame(self.init_window_name)
        self.top_frame.grid(row=0, column=0, columnspan=2)
        self.massage_label = Label(self.top_frame, text="提示区域", width=30, font="微软雅黑 15 bold")
        self.massage_label.grid(row=0, column=0, columnspan=2)

        # 左边-上边区域==============================================================
        self.install_frame = Frame(self.init_window_name)
        self.install_frame.grid(row=1, column=0, sticky="N")

        # 模式选择区域-------------------------------------------------------------
        self.mode_frame = LabelFrame(self.install_frame, text="安装模式选择：", width=self.width / 2)
        self.mode_frame.grid(row=0, column=0, sticky="E", padx=6)
        self.mode_data = StringVar()
        self.mode_data.set("仅安装")
        mode_list = ["仅安装", "批量出包安装(自动)", "批量出包安装(手动)"]
        radiobutton_w = int(60 / len(mode_list))
        for m in range(len(mode_list)):
            Radiobutton(self.mode_frame, text=mode_list[m], variable=self.mode_data, value=mode_list[m], indicatoron=0,
                        width=radiobutton_w).grid(row=0, column=m, sticky="E")
        # 包名区域----------------------
        self.app_key_frame = LabelFrame(self.install_frame, text="包名：", width=self.width / 2)
        self.app_key_frame.grid(row=1, column=0)
        self.app_key_var = StringVar()
        self.app_key_var.set(app_key)
        self.app_key_entry = Entry(self.app_key_frame, textvariable=self.app_key_var, width=51)
        self.app_key_entry.grid(row=0, column=0, padx=3, ipady=3)
        self.app_key_button = Button(self.app_key_frame, text="设置", width=10, command=self.app_key_setting)
        self.app_key_button.grid(row=0, column=1)
        # 文件地址区域-------------------------------------------------------------
        self.file_path_frame = LabelFrame(self.install_frame, text="文件地址：")
        self.file_path_frame.grid(row=2, column=0)
        self.file_label = Label(self.file_path_frame, text="（将文件拖入窗口任意位置即可获取文件地址）")
        self.file_label.grid(row=0, column=0, sticky="W")
        # 文本框清空按钮
        self.clear_button = Button(self.file_path_frame, text="清空", height=1, width=10, command=self.text_clear)
        self.clear_button.grid(row=0, column=0, sticky="E")
        # 文本框
        self.file_path_text = Text(self.file_path_frame, width=61, height=4)
        self.file_path_text.grid(row=1, column=0, padx=5, pady=5, ipadx=5, ipady=5)

        # 右边-上边区域==============================================================
        # 设备选择区域-------------------------------------------------------------
        self.devices_frame = LabelFrame(self.install_frame, text="设备选择：（不选默认所有）", width=66)
        self.devices_frame.grid(row=0, column=1, sticky="E", padx=10, rowspan=2)
        # 设备复选框
        self.checkboxes = {}
        self.devices_button = []
        self.devices = []
        self.devices_checkbutton()
        # 设备刷新按钮
        self.refresh_button = Button(self.devices_frame, text="刷新", width=8, command=self.devices_checkbutton)
        self.refresh_button.grid(row=0, column=0, sticky="E", ipadx=1, ipady=1)

        # 按钮区域-------------------------------------------------------------
        self.button_frame = Frame(self.install_frame)
        self.button_frame.grid(row=2, column=1, padx=10, pady=10)
        # 开始按钮
        self.install_button = Button(self.button_frame, text="核验思维默认数据", width=22,
                                     command=lambda: self.thread_it(self.default_check))
        self.install_button.grid(row=0, column=0, padx=10)
        self.install_button = Button(self.button_frame, text="安装", width=22,
                                     command=lambda: self.thread_it(self.run))
        self.install_button.grid(row=0, column=1, padx=10)

        self.choose_devices_frame = LabelFrame(self.button_frame, text="选中设备上操作：")
        self.choose_devices_frame.grid(row=1, column=0, pady=10, columnspan=2)

        self.debug_button = Button(self.choose_devices_frame, text="开启正式线调试模式", width=21,
                                   command=lambda: self.thread_it(self.debug_commend))
        self.debug_button.grid(row=0, column=0, pady=5)
        self.delete_button = Button(self.choose_devices_frame, text="卸载", width=15,
                                    command=lambda: self.thread_it(self.delete_commend))
        self.delete_button.grid(row=0, column=1, pady=5)
        self.delete_button = Button(self.choose_devices_frame, text="清空", width=15,
                                    command=lambda: self.thread_it(self.clear_commend))
        self.delete_button.grid(row=0, column=2, pady=5)

        self.setting_button = Button(self.choose_devices_frame, text="打开语言设置", width=15,
                                     command=lambda: self.thread_it(self.setting_commend))
        self.setting_button.grid(row=0, column=3, pady=5)
        # 下方区域==============================================================
        self.log_frame = LabelFrame(self.init_window_name, text="任务列表：")
        self.log_frame.grid(row=2, column=0, padx=15, columnspan=2)
        self.task_label = Label(self.log_frame, text="（单击文件地址可复制）")
        self.task_label.grid(row=0, column=0, sticky="W")
        # 清空按钮
        self.clear_button = Button(self.log_frame, text="清空", height=1, width=10, command=self.canvas_clear)
        self.clear_button.grid(row=0, column=0, sticky="E", columnspan=2)

        # 任务列表
        self.task_canvas = Canvas(self.log_frame, width=self.width - 80, height=200, bg="white")
        self.task_canvas.grid(row=1, column=0, padx=5, columnspan=2)
        self.task_canvas_header = {"序号": 60, "状态": 120, "设备": 200, "文件": 550, "操作": 900}
        self.y = 20  # 标题高度
        self.add_canvas()
        # 设置滚动区域
        self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))
        # 添加滚动条
        scrollbar = Scrollbar(self.log_frame)
        scrollbar.grid(row=1, column=2, sticky="ns")
        scrollbar.configure(command=self.task_canvas.yview)
        self.task_canvas.configure(yscrollcommand=scrollbar.set)
        # 任务列表有变化时，刷新列表
        task_list_observer.register(self.add_canvas)

        # 继续按钮
        self.continue_button = Button(self.log_frame, text="批量任务继续进行", height=1, width=20, command=self.is_continue)
        self.isContinue = False
        # 取消按钮
        self.cancel_button = Button(self.log_frame, text="取消后续任务", height=1, width=20, command=self.is_cancel)
        self.isCancel = False
        # self.continue_button.grid(row=0, column=0, sticky="E", ipadx=3)
        # self.cancel_button.grid(row=0, column=1, sticky="W", padx=3)

    def app_key_setting(self):
        global app_key
        app_key = self.app_key_entry.get()

    @staticmethod
    def open_commend(task):
        open_app(task['设备ID'], task['app_id'][0])

    @staticmethod
    def canvas_clear():
        task_clear()

    def copy_to_clipboard(self, widget):
        selected_text = widget.cget('text')
        widget.clipboard_clear()
        widget.clipboard_append(selected_text)
        self.massage_label.config(text="已复制文件地址")

    def setting_commend(self):
        select_devices = self.devices_checkbutton_get()
        if select_devices:
            for d in select_devices:
                self.thread_it(setting_debug, d)
                task_control(app_key, d, "开启语言设置")
        else:
            self.massage_label.config(text="没有选中设备")

    def add_canvas(self):
        global task_list
        self.task_canvas.delete("all")
        self.y = 20  # 标题高度
        for key, value in self.task_canvas_header.items():
            self.task_canvas.create_text(value, self.y, text=key, anchor="center")
        for i in task_list:
            a1 = -(-len(i['文件']) // 86)
            self.y = self.y + 30 + a1 * 3
            if '成功' in i['状态']:
                fill_color = 'green'
            elif '失败' in i['状态']:
                fill_color = 'red'
            else:
                fill_color = 'black'
            self.task_canvas.create_text(self.task_canvas_header["序号"], self.y, text=i['序号'])
            self.task_canvas.create_text(self.task_canvas_header["状态"], self.y, text=i['状态'], fill=fill_color)
            self.task_canvas.create_text(self.task_canvas_header["设备"], self.y, text=i['设备'])
            file_label = Label(self.task_canvas, text=i['文件'], wraplength=580, foreground="blue", cursor="hand2",
                               bg="white")
            file_label.bind('<Button-1>', lambda event: self.copy_to_clipboard(file_label))
            self.task_canvas.create_window(self.task_canvas_header["文件"], self.y, width=580, window=file_label)

            retry_button = Button(self.task_canvas, text='克隆', command=lambda i2=i: self.clone_task(i2))
            self.task_canvas.create_window(self.task_canvas_header['操作'] - 20, self.y, window=retry_button)
            if i['操作']:
                for b in i['操作']:
                    if b == "打开":
                        button = Button(self.task_canvas, text=b, command=lambda i2=i: self.open_commend(i2))
                        self.task_canvas.create_window(self.task_canvas_header['操作'] + 20, self.y, window=button)
                    elif b == "日志":
                        if i['日志']:
                            button = Button(self.task_canvas, text=b, command=lambda i2=i: self.show_log(i2))
                            self.task_canvas.create_window(self.task_canvas_header['操作'] + 20, self.y, window=button)
            self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))

    @staticmethod
    def show_log(task):
        def state_str(state):
            if state == 0:
                return "成功"
            else:
                return "失败"

        def level_conunt_text(count):
            for i in count:
                if i["level"] == "0":
                    level_o_str = {"0": "未选阶段课程", "1": "未入园", "2": "小班", "3": "中班", "4": "大班"}
                    log_text.insert("end", "体验岛阶段课程数量：" + "\n", "标题")
                    for key, value in i["count"].items():
                        log_text.insert("end", level_o_str[key] + ":" + str(value) + "\n")
                elif i["level"] == "趣味拓展-0":
                    level_o_str = {"0": "未选阶段课程", "1": "未入园", "2": "小班", "3": "中班", "4": "大班"}
                    log_text.insert("end", "趣味拓展各阶段免费课程数量：" + "\n", "标题")
                    for key, value in i["count"].items():
                        log_text.insert("end", level_o_str[key] + ":" + str(value) + "\n")
                else:
                    log_text.insert("end", "阶段-" + i["level"] + "：课程数量 " + str(i["count"]) + "\n")

                if i["error"]:
                    log_text.insert("end", "海外存在MV环节的课程：" + str(i["error"]) + "\n")
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

        log_text.insert("1.0", "========总状态========\n", "标题")
        log_text.insert("end", "核验状态：" + state_str(log["state"]), state_str(log["state"]))
        log_text.insert("end", "   信息：" + log["message"] + "\n")

        log_text.insert("end", "========默认图片========\n", "标题")
        log_text.insert("end", "核验状态：" + state_str(log["data"]["image"]["state"]),
                        state_str(log["data"]["image"]["state"]))
        log_text.insert("end", "  信息：" + log["data"]["image"]["message"] + "  图片数量：" + str(
            log["data"]["image"]["data"]) + "\n")

        log_text.insert("end", "========默认子包========\n", "标题")
        log_text.insert("end", "核验状态：" + state_str(log["data"]["default_game"]["state"]),
                        state_str(log["data"]["default_game"]["state"]))
        log_text.insert("end", "  信息：" + log["data"]["default_game"]["message"] + "  默认子包信息：" + str(
            log["data"]["default_game"]["data"]) + "\n")

        log_text.insert("end", "========首页默认数据（简体中文）========\n", "标题")
        log_text.insert("end", "核验状态：" + state_str(log["data"]["package_config_zh"]["state"]),
                        state_str(log["data"]["package_config_zh"]["state"]))
        log_text.insert("end", "   信息：" + log["data"]["package_config_zh"]["message"] + "\n")
        level_conunt_text(log["data"]["package_config_zh"]["data"])

        log_text.insert("end", "========首页默认数据（国际化语言）========\n", "标题")
        package_config_lang = log["data"]["package_config_lang"]
        log_text.insert("end", "核验状态：" + state_str(package_config_lang["state"]),
                        state_str(package_config_lang["state"]))
        log_text.insert("end", "   信息：" + package_config_lang["message"] + "\n")
        if package_config_lang["file_count"] and package_config_lang["random_file"]:
            log_text.insert("end", "总文件数量：" + str(package_config_lang["file_count"]) + "   " + "抽取的国际化文件：" +
                            package_config_lang["random_file"] + "\n")
            level_conunt_text(package_config_lang["data"])

        log_text.insert("end", "========趣味拓展数据（简体中文）========\n", "标题")
        log_text.insert("end", "核验状态：" + state_str(log["data"]["package_config_expand_zh"]["state"]),
                        state_str(log["data"]["package_config_expand_zh"]["state"]))
        log_text.insert("end", "   信息：" + log["data"]["package_config_expand_zh"]["message"] + "\n")
        level_conunt_text(log["data"]["package_config_expand_zh"]["data"])

        log_text.insert("end", "========趣味拓展数据（国际化语言）========\n", "标题")
        package_config_expand_lang = log["data"]["package_config_expand_lang"]
        log_text.insert("end", "核验状态：" + state_str(package_config_expand_lang["state"]),
                        state_str(package_config_expand_lang["state"]))
        log_text.insert("end", "   信息：" + package_config_expand_lang["message"] + "\n")
        if package_config_expand_lang["file_count"] and package_config_expand_lang["random_file"]:
            log_text.insert("end", "总文件数量：" + str(package_config_expand_lang["file_count"]) + "   " + "抽取的国际化文件：" +
                            package_config_expand_lang["random_file"] + "\n")
            level_conunt_text(package_config_expand_lang["data"])

        log_text.configure(state="disabled")

    def clone_task(self, task):
        if '安装' in task['状态']:
            self.thread_it(run_install, task['文件'], [task['设备ID']])
        elif '卸载' in task['状态']:
            self.thread_it(self.delete_commend)
        elif '调试' in task['状态']:
            self.thread_it(release_debug, task['设备ID'])
            task_control("", task['设备ID'], "开启调试")
        elif '清空' in task['状态']:
            self.thread_it(clear_app, task['设备ID'], task['app_id'])
            task_control(app_id=task['app_id'], path=task['app_id'], device=task['设备ID'], status="清空")
        elif '核验' in task['状态']:
            task_id = task_control(task['文件'], "", "核验包数据")
            result = DefaultCheck(task['文件']).main()
            if result["state"] == 0:
                task_control(task_id=task_id, path=task['文件'], device="", status="核验包成功", log=result, commend=["日志"])
            elif result["state"] == -1:
                task_control(task_id=task_id, path=task['文件'], device="", status="核验包失败", log=result, commend=["日志"])

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

    def debug_commend(self):
        select_devices = self.devices_checkbutton_get()
        if select_devices:
            for d in select_devices:
                self.thread_it(release_debug, d)
                task_control("", d, "开启调试")
        else:
            self.massage_label.config(text="没有选中设备")

    def delete_commend(self):
        # 卸载安装包
        def delete_task(device, app_id):
            # 卸载任务管理
            task_id = task_control(app_id, device, "卸载中")
            result = uninstall(device, app_id)
            if result:
                task_control(task_id=task_id, path=app_id, device=device, status="卸载成功")
            else:
                task_control(task_id=task_id, path=app_id, device=device, status="卸载失败")

        select_devices = self.devices_checkbutton_get()
        if select_devices:
            for d in select_devices:
                global app_key
                packages = get_packages_list(d)
                if app_key in packages:
                    self.thread_it(delete_task, d, app_key)
                else:
                    task_control(app_key, d, "设备上无包")
        else:
            self.massage_label.config(text="没有选中设备")

    def clear_commend(self):
        select_devices = self.devices_checkbutton_get()
        if select_devices:
            for d in select_devices:
                self.thread_it(clear_app, d, app_key)
                task_control(app_key, d, "清空")
        else:
            self.massage_label.config(text="没有选中设备")

    def default_check(self):

        file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
        file_list = get_adress(file_path_data)

        for index, f in enumerate(file_list):
            task_id = task_control(f, "", "核验包数据")
            self.massage_label.config(text="检测默认数据，第" + str(index + 1) + "个安装包")
            result = DefaultCheck(f).main()
            if result["state"] == 0:
                task_control(task_id=task_id, path=f, device="", status="核验包成功", log=result, commend=["日志"])
            elif result["state"] == -1:
                task_control(task_id=task_id, path=f, device="", status="核验包失败", log=result, commend=["日志"])
        self.massage_label.config(text="检测默认数据完成")

    def run(self):
        file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
        if len(file_path_data) <= 0:
            self.massage_label.config(text="请填写正确文件路径")
        elif not self.devices:
            self.massage_label.config(text="当前没有连接的设备")
        else:
            select_devices = self.devices_checkbutton_get()
            file_list = get_adress(file_path_data)
            app_key = None
            for index, f in enumerate(file_list):
                if self.isCancel:
                    self.isCancel = False
                    break
                if self.mode_data.get() == "仅安装":
                    self.thread_it(run_install, f, select_devices)
                else:
                    self.massage_label.config(text="批量任务进行中：第" + str(index + 1) + "个安装包开始")
                    app_key = run_install(f, select_devices, app_key, True)
                    self.massage_label.config(text="批量任务进行中：第" + str(index + 1) + "个安装包结束")
                    if index != len(file_list) - 1 and self.mode_data.get() == "批量出包安装(手动)":
                        self.continue_button.grid(row=0, column=0, sticky="E", ipadx=3)
                        self.cancel_button.grid(row=0, column=1, sticky="W", padx=3)
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

    def text_clear(self):
        # 清空输入框
        self.file_path_text.delete("1.0", "end")


def gui_start():
    init_window = Tk()  # 实例化出一个父窗口
    InstallApp(init_window)
    init_window.mainloop()


if __name__ == '__main__':
    gui_start()
