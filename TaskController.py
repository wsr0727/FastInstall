from copy import deepcopy
from Glob import *
import re
from pathlib import Path


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


def task_control(path=None, device="", status="未开始", app_id=None, task_id=0, log=None, file_name=None, version=None):
    """
    用于更新任务列表task_list数据。
    模板{"序号": 0, "状态": status, "设备": device, "设备ID": device, "文件": path, "操作": [],"app_id"：“”，“日志”：None}
    :param path:文件路径
    :param device: 设备ID
    :param status: 完成状态
    :param task_id: 任务ID
    :param app_id: 应用包名
    :param file_name: 文件名
    :param log: 日志
    :param version: 版本号
    :return:返回任务ID
    """
    # TODO 优化任务管理的实现方式
    task_list = glob.get_gl_task_list()
    device_name = [n[1] for n in glob.get_gl_devices() if device in n]
    if path:  # 地址不为空才判断
        file_name = Path(path).name
        result = get_file_name_info(file_name)
        app_id = result.get("app_key", app_id)
        version = result.get("version", version)
    if log:
        log = deepcopy(log)
    if task_id == 0:
        task_id = len(task_list) + 1
        task_list.insert(0, {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                             "文件名": file_name, "app_id": app_id, "日志": log, "版本号": version})
    else:
        for i in range(len(task_list)):
            if task_list[i]["序号"] == task_id:
                task_list[i] = {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                                "文件名": file_name, "app_id": app_id, "日志": log, "版本号": version}
                glob.set_gl_task_list(task_list)
                break

    task_list_observer.notify()  # 通知任务列表已更新
    return task_id


def task_clear():
    """
    清空任务列表
    """
    glob.set_gl_task_list([])
    task_list_observer.notify()  # 通知任务列表已更新


def get_file_name_info(file_name):
    """
    根据文件名获取包名、版本号
    :param file_name: 文件名
    :return: 包名 {"app_key": i}、版本{"version": version}，识别不到返回{}
    """
    file_name_str = file_name.split('-')
    pattern = r'[0-9]+\.[0-9]+\.*'
    result = {}
    for i in file_name_str:
        match = re.search(pattern, i)
        if match:
            version = i.replace('.apk', '').replace('.aab', '').replace('.ipa', '').replace('.', '')  # 适配iOS和安卓不同的版本号
            result.update({"version": version})
        if "com." in i:
            result.update({"app_key": i})
    return result


if __name__ == '__main__':
    # 代码调试
    file_name = r"com.sinyee.babybus.mathIII-app-store-2.05.0140-children.ipa"
    print(get_file_name_info(file_name))
