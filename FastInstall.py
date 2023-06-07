import os
import time
import logging
from tkinter import *
import windnd
import tkinter.scrolledtext as ScrolledText
import threading

# 打包指令 pyinstaller -F -w FastInstall.py

'''
快速安卓启动卸载
'''
# 日志设置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')

devices = []  # 当前连接设备


# 获取devices数量和名称
def get_devices_all():
    global devices
    devices = []
    try:
        for dName_ in os.popen('adb devices -l'):
            if "List of devices attached" not in dName_:
                name_list = dName_.split()
                devices.append([name_list[0], name_list[3].strip("model:")])
    except:
        pass
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
    logging.debug("正在安装的APK目录：" + adress)
    if os.path.isdir(adress):
        for f in os.listdir(adress):
            # 只装apk
            if ".apk" in f:
                adress_list.append('{}/{}'.format(adress, f))
    else:
        adress_list = [item for item in adress.split("\n") if ".apk" in item]
    return adress_list


# 卸载手机上所有应用
def uninstall(device, package_name):
    uninstall_command = os.popen('adb -s ' + device + " uninstall " + package_name).read()
    log_info = '包名：' + package_name + '  设备：' + str(device)
    if 'Success' in uninstall_command[-9:]:
        logging.info("【删除成功】：" + log_info)
    else:
        logging.error("【删除失败】" + log_info + "\n" + '原因:\n' + uninstall_command)


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


def run_install(path, devices_list, appkey=None, is_luncher=False):
    # 安装单个
    for device in devices_list:
        tast_id = task_control(path, device, "安装进行中")
        if appkey:
            uninstall(device, appkey)
        appkey_list = adb_install(device, path)  # 安装,获取包名
        if appkey_list:
            task_control(path, device, "安装成功", appkey_list[0], tast_id, commend=["打开"])
            if is_luncher:
                appkey = appkey_list[0][0]
                luncher_app(device, appkey)
        else:
            task_control(path, device, "安装失败", tast_id=tast_id, commend=[])
    return appkey


task_list = []


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


def task_clear():
    global task_list
    task_list.clear()
    task_list_observer.notify()  # 通知任务列表已更新


def task_control(path, device, status="未开始", app_id=None, tast_id=0, commend=[]):
    """
    用于更新任务列表task_list数据，模板{"序号": 0, "状态": status, "设备": device, "设备ID": device, "文件": path, "操作": [],"app_id"：“”}
    :param path:文件路径
    :param device: 设备ID
    :param status: 完成状态
    :param tast_id: 任务ID
    :return:返回任务ID
    """
    global task_list, devices
    device_name = [n[1] for n in devices if device in n]
    if tast_id == 0:
        tast_id = len(task_list) + 1
        task_list.insert(0, {"序号": tast_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path, "操作": commend,
                             "app_id": app_id})
    else:
        for i in range(len(task_list)):
            if task_list[i]["序号"] == tast_id:
                task_list[i] = {"序号": tast_id, "状态": status, "设备": device_name, "设备ID": device, "文件": path,
                                "操作": commend, "app_id": app_id}

    task_list_observer.notify()  # 通知任务列表已更新
    return tast_id


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

        # 左边区域==============================================================
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
                        width=radiobutton_w).grid(row=0, column=m, padx=1, sticky="E")

        # 文件地址区域-------------------------------------------------------------
        self.file_path_frame = LabelFrame(self.install_frame, text="文件地址：")
        self.file_path_frame.grid(row=1, column=0)
        # 文本框清空按钮
        self.clear_button = Button(self.file_path_frame, text="清空", height=1, width=10, command=self.text_clear)
        self.clear_button.grid(row=0, column=0, sticky="E")
        # 文本框
        self.file_path_text = Text(self.file_path_frame, width=61, height=4)
        self.file_path_text.grid(row=1, column=0, padx=5, pady=5, ipadx=5, ipady=5)

        # 设备选择区域-------------------------------------------------------------
        self.devices_frame = LabelFrame(self.install_frame, text="设备选择：", width=66)
        self.devices_frame.grid(row=0, column=1, sticky="E", padx=10)
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
        self.button_frame.grid(row=1, column=1, padx=10, pady=10)
        # 开始按钮
        self.install_button = Button(self.button_frame, text="所有设备上安装", width=22,
                                     command=lambda: self.thread_it(self.run, "all"))
        self.install_button.grid(row=0, column=0, padx=10)
        self.install_button = Button(self.button_frame, text="选中设备上安装", width=22,
                                     command=lambda: self.thread_it(self.run, "select"))
        self.install_button.grid(row=0, column=1, padx=10)

        self.choose_devices_frame = LabelFrame(self.button_frame, text="选中设备上操作：")
        self.choose_devices_frame.grid(row=1, column=0, pady=10, columnspan=2)

        self.debug_button = Button(self.choose_devices_frame, text="开启正式线调试模式", width=22,
                                   command=lambda: self.thread_it(self.debug_commend))
        self.debug_button.grid(row=0, column=0, pady=5)
        self.delete_button = Button(self.choose_devices_frame, text="卸载思维", width=22,
                                    command=lambda: self.thread_it(self.delete_commend))
        self.delete_button.grid(row=0, column=1, pady=5)
        self.delete_button = Button(self.choose_devices_frame, text="清空思维", width=22,
                                    command=lambda: self.thread_it(self.clear_commend))
        self.delete_button.grid(row=0, column=2, pady=5)
        # 右边区域==============================================================
        self.log_frame = LabelFrame(self.init_window_name, text="任务列表：")
        self.log_frame.grid(row=2, column=0, padx=15, columnspan=2)
        self.task_label = Label(self.log_frame, text="（单击文件地址可复制）")
        self.task_label.grid(row=0, column=0, sticky="W")
        # 清空按钮
        self.clear_button = Button(self.log_frame, text="清空", height=1, width=10, command=self.canvas_clear)
        self.clear_button.grid(row=0, column=0, sticky="E", columnspan=2)

        self.task_canvas = Canvas(self.log_frame, width=self.width - 80, height=200, bg="white")
        self.task_canvas.grid(row=1, column=0, padx=5, columnspan=2)
        # 绘制标题
        self.task_canvas_header = {"序号": 60, "状态": 120, "设备": 200, "文件": 550, "操作": 900}
        for key, value in self.task_canvas_header.items():
            self.task_canvas.create_text(value, 20, text=key, anchor="center")
        self.y = 20
        # 设置滚动区域
        self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))
        # 添加滚动条
        scrollbar = Scrollbar(self.log_frame)
        scrollbar.grid(row=1, column=2, sticky="ns")
        scrollbar.configure(command=self.task_canvas.yview)
        self.task_canvas.configure(yscrollcommand=scrollbar.set)
        # 任务列表有变化时，刷新列表
        task_list_observer.register(self.add_canvas)

        # 右边-下方区域==============================================================
        # 继续按钮
        self.continue_button = Button(self.log_frame, text="批量任务继续进行", height=1, width=20, command=self.is_continue)
        self.isContinue = False
        # 取消按钮
        self.cancel_button = Button(self.log_frame, text="取消后续任务", height=1, width=20, command=self.is_cancel)
        self.isCancel = False
        # self.continue_button.grid(row=0, column=0, sticky="E", ipadx=3)
        # self.cancel_button.grid(row=0, column=1, sticky="W", padx=3)

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

    def add_canvas(self):
        global task_list
        print("任务列表：", task_list)
        self.task_canvas.delete("all")
        for key, value in self.task_canvas_header.items():
            self.task_canvas.create_text(value, 20, text=key, anchor="center")
        self.y = 20
        for i in task_list:
            a1 = -(-len(i['文件']) // 86)
            self.y = self.y + 30 + a1 * 3
            if '成功' in i['状态']:
                fill_color = 'green'
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

            for b in i['操作']:
                button = Button(self.task_canvas, text=b, command=lambda i2=i: self.open_commend(i2))
                self.task_canvas.create_window(self.task_canvas_header['操作'] + 20, self.y, window=button)

            self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))

    def clone_task(self, task):
        if '安装' in task['状态']:
            self.thread_it(run_install, task['文件'], [task['设备ID']])
        elif '卸载' in task['状态']:
            self.thread_it(uninstall, task['设备ID'], "com.sinyee.babybus.mathIII")
            task_control("com.sinyee.babybus.mathIII", task['设备ID'], "卸载思维")
        elif '调试' in task['状态']:
            self.thread_it(release_debug, task['设备ID'])
            task_control("", task['设备ID'], "开启调试")
        elif '清空' in task['状态']:
            self.thread_it(clear_app, task['设备ID'], "com.sinyee.babybus.mathIII")
            task_control("com.sinyee.babybus.mathIII", task['设备ID'], "清空思维")

    def devices_checkbutton(self):
        # 构建复选框
        while self.devices_button:
            check_btn = self.devices_button.pop()
            check_btn.destroy()
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
        # 获取复选框选中数据
        select_devices = []
        for i in self.checkboxes:
            if self.checkboxes[i].get():
                select_devices.append(self.devices[i][0])
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
        select_devices = self.devices_checkbutton_get()
        if select_devices:
            for d in select_devices:
                self.thread_it(uninstall, d, "com.sinyee.babybus.mathIII")
                task_control("com.sinyee.babybus.mathIII", d, "卸载思维")
        else:
            self.massage_label.config(text="没有选中设备")

    def clear_commend(self):
        select_devices = self.devices_checkbutton_get()
        if select_devices:
            for d in select_devices:
                self.thread_it(clear_app, d, "com.sinyee.babybus.mathIII")
                task_control("com.sinyee.babybus.mathIII", d, "清空思维")
        else:
            self.massage_label.config(text="没有选中设备")

    def run(self, devices_mode):
        file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
        if len(file_path_data) <= 0:
            self.massage_label.config(text="请填写正确文件路径")
        elif not self.devices:
            self.massage_label.config(text="当前没有连接的设备")
        else:
            if devices_mode == "select":
                select_devices = self.devices_checkbutton_get()
            else:
                select_devices = [d[0] for d in self.devices]

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
    set_window = InstallApp(init_window)
    init_window.mainloop()


if __name__ == '__main__':
    gui_start()
