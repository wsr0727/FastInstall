from copy import deepcopy
from Glob import *


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
    task_list = glob.get_gl_task_list()
    device_name = [n[1] for n in glob.get_gl_devices() if device in n]
    if path:  # 地址不为空才判断
        result = get_app_key(path)
        if result:
            file_name = result[0]
            app_id = result[1]
    if log:
        log = deepcopy(log)
    if task_id == 0:
        task_id = len(task_list) + 1
        task_list.insert(0, {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                             "操作": commend, "文件名": file_name, "app_id": app_id, "日志": log})
    else:
        for i in range(len(task_list)):
            if task_list[i]["序号"] == task_id:
                task_list[i] = {"序号": task_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                                "文件名": file_name, "操作": commend, "app_id": app_id, "日志": log}
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


def get_app_key(path):
    # 根据文件获取包名
    file_name = path.split('\\')[-1]
    if "/" in file_name:
        file_name = file_name.split('/')[-1]
    file_name_str = file_name.split('-')
    for i in file_name_str:
        if "com." in i:
            return file_name, i
