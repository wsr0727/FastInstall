from tkinter import *
import windnd
import threading
from tkinter import ttk
from DefaultCheck import DefaultCheck
from AdbCommand import *
from Cache import *
from FrameUI import show_log
from TaskController import *
from Glob import *
from LanguageChecker import show_lang_window
from PackageDataChecker import show_data_check_window
import requests
import json

# 日志设置
# logging.basicConfig(filename='test.log', level=logging.DEBUG,
#                     format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')
# 打包指令 pyinstaller -F -w FastInstall.py

app_key, input_list, app_key_histroy, ip_history = get_cache()  # 初始化缓存
glob.set_gl_input_list(input_list)
glob.set_gl_app_key(app_key)
glob.set_gl_app_key_histroy(app_key_histroy)
glob.set_gl_ip_history(ip_history)


# ---界面UI-----------------------------------------------
class InstallApp:
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.init_window_name.title("超好用的测试工具  3.00.11")
        self.width = 1000
        # self.height = 520
        self.height = 530  # 加上”更多“按钮的高度
        self.init_window_name.geometry(str(self.width) + 'x' + str(self.height) + '+15+30')
        windnd.hook_dropfiles(self.init_window_name, func=self.dragg)

        # 创建菜单栏
        self.menubar = Menu(self.init_window_name)

        # 创建文件菜单
        self.tools_menu = Menu(self.menubar, tearoff=0)
        self.tools_menu.add_command(label="国际化音频校验", command=show_lang_window)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="数据核验工具", command=show_data_check_window)
        self.tools_menu.add_separator()
        self.menubar.add_cascade(label="工具箱", menu=self.tools_menu)
        self.init_window_name.config(menu=self.menubar)

        # 顶部区域==============================================================
        self.top_frame = Frame(self.init_window_name)
        self.top_frame.grid(row=0, column=0)
        self.massage_label = Label(self.top_frame, text="提示区域", width=75, font="微软雅黑 15 bold")
        self.massage_label.grid(row=0, column=0, sticky="N")

        # 中间区域==============================================================
        self.install_frame = Frame(self.init_window_name)
        self.install_frame.grid(row=1, column=0, sticky="N")

        # 中间-左边区域==============================================================
        # 模式选择区域-------------------------------------------------------------
        self.mode_frame = LabelFrame(self.install_frame, text="安装模式选择：")
        self.mode_frame.grid(row=0, column=0)
        self.mode_data = StringVar()
        self.mode_data.set("仅安装")
        mode_list = ["仅安装", "批量出包安装(自动)", "批量出包安装(手动)"]
        radiobutton_w = 65 // len(mode_list)
        for m, mode in enumerate(mode_list):
            Radiobutton(self.mode_frame, text=mode, variable=self.mode_data, value=mode,
                        indicatoron=False, width=radiobutton_w).grid(row=0, column=m)
        # 包名区域----------------------
        self.app_key_frame = LabelFrame(self.install_frame, text="包名：（支持打开网页）")
        self.app_key_frame.grid(row=1, column=0)
        self.app_key_var = StringVar()
        self.app_key_var.set(app_key)
        self.app_key_entry = ttk.Combobox(self.app_key_frame, textvariable=self.app_key_var, width=45,
                                          values=glob.get_gl_app_key_histroy())
        self.app_key_entry.grid(row=0, column=0)
        self.app_key_entry.bind("<<ComboboxSelected>>", self.app_key_select)
        self.app_key_button = Button(self.app_key_frame, text="打开", width=8,
                                     command=lambda: self.thread_it(self.devices_manager, "open"))
        self.app_key_button.grid(row=0, column=1)
        self.app_key_button = Button(self.app_key_frame, text="设置", width=8,
                                     command=lambda: self.app_key_setting(self.app_key_entry.get()))
        self.app_key_button.grid(row=0, column=2)

        # 文件地址区域-------------------------------------------------------------
        self.file_path_frame = LabelFrame(self.install_frame, text="文件地址（将文件拖入窗口任意位置即可获取文件地址）：")
        self.file_path_frame.grid(row=2, column=0)
        self.file_app_button = Button(self.file_path_frame, text="识别包名并设置", width=15,
                                      command=self.file_to_app_key)
        self.file_app_button.grid(row=0, column=0, sticky="W")

        self.course_defaule_button = Button(self.file_path_frame, text="科学默认数据", width=10,
                                            command=lambda: self.thread_it(self.default_check, None, "course"))
        self.course_defaule_button.grid(row=0, column=0)

        # 核验思维默认数据
        self.defaule_check_button = Button(self.file_path_frame, text="核验思维默认数据", width=15,
                                           command=lambda: self.thread_it(self.default_check))
        self.defaule_check_button.grid(row=0, column=0, sticky="E")

        # 文本框
        self.file_path_text = Text(self.file_path_frame, width=67, height=5)
        self.file_path_text.grid(row=1, column=0)

        # 中间-右边区域==============================================================
        # 设备选择区域-------------------------------------------------------------
        self.devices_frame = LabelFrame(self.install_frame, text="设备选择：（不选默认所有）")
        self.devices_frame.grid(row=0, column=1, rowspan=2)

        # WiFi代理
        self.wifi_proxy_frame = Frame(self.devices_frame)
        self.wifi_proxy_frame.grid(row=0, column=0, sticky="W")

        self.ip_label = Label(self.wifi_proxy_frame, text="设置全局代理 IP：")
        self.ip_label.grid(row=0, column=0, padx=4)
        self.wifi_ip_var = StringVar()
        if glob.get_gl_ip_history():
            self.wifi_ip_var.set(glob.get_gl_ip_history()[0])
        self.wifi_ip_entry = ttk.Combobox(self.wifi_proxy_frame, textvariable=self.wifi_ip_var, width=13,
                                          values=glob.get_gl_ip_history())
        self.wifi_ip_entry.grid(row=0, column=1)
        self.wifi_port_label = Label(self.wifi_proxy_frame, text=":")
        self.wifi_port_label.grid(row=0, column=2, padx=1)
        self.wifi_port_var = StringVar()
        self.wifi_port_var.set("8888")
        self.wifi_port_entry = Entry(self.wifi_proxy_frame, textvariable=self.wifi_port_var, width=6)
        self.wifi_port_entry.grid(row=0, column=3)
        self.proxy_open_button = Button(self.wifi_proxy_frame, text="开启",
                                        command=lambda: self.thread_it(self.devices_manager,
                                                                       [self.wifi_proxy_set, True, "开启WiFi代理"]))
        self.proxy_open_button.grid(row=0, column=4, padx=1)
        self.proxy_off_button = Button(self.wifi_proxy_frame, text="关闭",
                                       command=lambda: self.thread_it(self.devices_manager,
                                                                      [self.wifi_proxy_set, False, "关闭WiFi代理"]))
        self.proxy_off_button.grid(row=0, column=5, padx=1)

        # 设备刷新按钮
        self.refresh_button = Button(self.devices_frame, text="刷新设备", width=8, command=self.devices_checkbutton)
        self.refresh_button.grid(row=0, column=0, sticky="E")
        self.devices_checkFrame = Frame(self.devices_frame)
        self.devices_checkFrame.grid(row=1, column=0)
        # 设备复选框
        self.checkboxes = {}
        self.devices_button = []
        self.devices = []
        self.thread_it(self.devices_checkbutton)

        # 按钮区域-------------------------------------------------------------
        self.button_frame = Frame(self.install_frame)
        self.button_frame.grid(row=2, column=1, padx=10)
        self.choose_app_frame = LabelFrame(self.button_frame, text="应用管理：")
        self.choose_app_frame.grid(row=0, column=0, columnspan=2)
        # 开始按钮
        self.delete_button = Button(self.choose_app_frame, text="卸载应用", width=15,
                                    command=lambda: self.thread_it(self.devices_manager, "delete"))
        self.delete_button.grid(row=0, column=0)
        self.clear_data_button = Button(self.choose_app_frame, text="清空应用缓存", width=15,
                                        command=lambda: self.thread_it(self.devices_manager,
                                                                       [clear_app, self.app_key_entry.get(),
                                                                        "清空应用"]))

        self.clear_data_button.grid(row=0, column=1)
        self.install_button = Button(self.choose_app_frame, text="安装", width=18,
                                     command=lambda: self.thread_it(self.run))
        self.install_button.grid(row=0, column=2)

        self.choose_devices_frame = LabelFrame(self.button_frame, text="指令管理：")
        self.choose_devices_frame.grid(row=1, column=0, sticky="e")

        self.debug_button = Button(self.choose_devices_frame, text="开启调试模式", width=15,
                                   command=lambda: self.devices_manager([release_debug, True, "开启调试模式"]))
        self.debug_button.grid(row=0, column=0)

        self.debug_button = Button(self.choose_devices_frame, text="关闭调试模式", width=15,
                                   command=lambda: self.devices_manager([release_debug, False, "关闭调试模式"]))
        self.debug_button.grid(row=0, column=1)

        self.setting_button = Button(self.choose_devices_frame, text="打开广告日志", width=14,
                                     command=lambda: self.thread_it(self.devices_manager,
                                                                    [ad_debug, True, "开启ad日志"]))
        self.setting_button.grid(row=0, column=2)

        self.setting_frame = LabelFrame(self.button_frame, text="打开设置页面：")
        self.setting_frame.grid(row=1, column=1, sticky="e")

        self.setting_lang = Button(self.setting_frame, text="语言", width=4,
                                   command=lambda: self.thread_it(self.devices_manager,
                                                                  [setting_debug, "语言", "打开语言页面"]))
        self.setting_lang.grid(row=0, column=0)
        self.setting_data = Button(self.setting_frame, text="时间", width=4,
                                   command=lambda: self.thread_it(self.devices_manager,
                                                                  [setting_debug, "时间", "打开时间页面"]))
        self.setting_data.grid(row=0, column=1)
        self.setting_WiFi = Button(self.setting_frame, text="WiFi", width=4,
                                   command=lambda: self.thread_it(self.devices_manager,
                                                                  [setting_debug, "WiFi", "打开WiFi页面"]))
        self.setting_WiFi.grid(row=0, column=2)
        # 下方区域==============================================================
        self.log_frame = LabelFrame(self.init_window_name, text="任务列表：(双击任务可复制文件地址)")
        self.log_frame.grid(row=2, column=0, padx=18, sticky="n")

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

        tree_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.tree.yview)
        tree_scrollbar.grid(row=0, column=1, sticky="nsw")

        # 将滚动条与 Treeview 关联
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.log_button_frame = Frame(self.log_frame)
        self.log_button_frame.grid(row=0, column=2, sticky="ne")
        btn_w = 12  # 操作按钮区域宽度
        btn_h = 1  # 操作按钮区域高度
        # 清空按钮
        self.clear_button = Button(self.log_button_frame, text="清空任务列表", height=btn_h, width=btn_w,
                                   command=self.clear_tree)
        self.clear_button.grid(row=0, column=0)

        buttons = [("打开", "open"),
                   ("克隆", "clone"),
                   ("日志", "log"),
                   ("设置包名", "set_app_key")]

        for row, (text, command) in enumerate(buttons, start=1):
            Button(self.log_button_frame, text=text, height=btn_h, width=btn_w,
                   command=lambda cmd=command: self.task_commend(cmd)).grid(row=row, column=0)
        # 继续按钮
        self.continue_button = Button(self.log_button_frame, text="批量任务继续", height=btn_h, width=btn_w,
                                      command=self.is_continue)
        self.isContinue = False
        # 取消按钮
        self.cancel_button = Button(self.log_button_frame, text="取消后续任务", height=btn_h, width=btn_w,
                                    command=self.is_cancel)
        self.isCancel = False
        # self.continue_button.grid(row=5, column=0)
        # self.cancel_button.grid(row=6, column=0)

        # 扩展区域==============================================================
        # 拓展入口开关
        self.expand_Label = Label(self.init_window_name, text="\\v/ 更多")
        self.expand_Label.config(foreground='blue', font=('微软雅黑', 10, 'underline'))
        self.expand_off_Label = Label(self.init_window_name, text="/^\\ 收起")
        self.expand_off_Label.config(foreground='blue', font=('微软雅黑', 10, 'underline'))
        self.expand_Label.grid(row=3, column=0, sticky="E", ipadx=15)
        self.expand_Label.bind("<Button-1>", self.expand_show)
        self.expand_off_Label.bind("<Button-1>", self.expand_close)

        # 拓展-输入字符
        self.expand_frame = LabelFrame(self.init_window_name, text="指定设备上输入字符：")
        self.input_Label = Label(self.expand_frame, text="内容：")
        self.input_var = StringVar()
        self.input_entry = Entry(self.expand_frame, textvariable=self.input_var, width=40)
        self.input_button = Button(self.expand_frame, text="输入",
                                   command=lambda: self.thread_it(self.devices_manager,
                                                                  [self.input_task, "", "输入字符"]))
        # 拓展-输入字符-输入历史
        self.input_histroy = ttk.Treeview(self.expand_frame)
        self.input_histroy.config(height=4)
        self.input_histroy.column("#0", width=340, anchor="w")
        self.input_histroy.heading("#0", text="输入历史(只保存20条，双击可再次输入，右击可选删除)")
        if glob.get_gl_input_list():
            for h in glob.get_gl_input_list():
                self.input_histroy.insert("", "end", text=h)
        self.input_histroy.bind("<Double-Button-1>", self.click_to_input)
        self.input_histroy_scrollbar = ttk.Scrollbar(self.expand_frame, orient="vertical",
                                                     command=self.input_histroy.yview)
        self.input_histroy.configure(yscrollcommand=self.input_histroy_scrollbar.set)

        # 拓展-输入字符-输入历史-右键菜单
        self.input_histroy_menu = Menu(self.input_histroy, tearoff=0)
        self.input_histroy_menu.add_command(label='删除', command=self.delete_selected_item)
        self.input_histroy.bind('<Button-3>', self.show_context_menu)

        # 拓展-输入字符-按钮
        self.input_CaptchaNo_test = Button(self.expand_frame, text="测试线输入验证码", width=15,
                                           command=lambda: self.thread_it(self.input_captcha_no, "test"))
        self.input_CaptchaNo = Button(self.expand_frame, text="正式线输入验证码", width=15,
                                      command=lambda: self.thread_it(self.input_captcha_no))
        self.input_CaptchaNo_label = Label(self.expand_frame, text="先选手机号再点")

    def file_to_app_key(self):
        file_path_data = str(self.file_path_text.get("1.0", "end")).rstrip().lstrip()
        if not file_path_data:  # 地址不为空才判断
            self.massage_label.config(text="文件地址为空")
            return
        result = get_file_name_info(file_path_data)
        if not result.get("app_key"):
            self.massage_label.config(text="识别失败")
            return
        self.app_key_setting(result.get("app_key"))

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
        self.input_histroy.grid(row=1, column=0, columnspan=4, padx=5, sticky="W")
        self.input_histroy_scrollbar.grid(row=1, column=2, sticky="nse")
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
        self.input_histroy_scrollbar.grid_remove()
        self.input_CaptchaNo.grid_remove()

    def input_histroy_list(self, text="", save=True):
        # 处理输入历史的列表控制，默认保存text,也支持删除text
        text_list = glob.get_gl_input_list()
        if text in text_list:
            text_list.remove(text)
        else:
            self.input_histroy.insert("", 0, text=text)

        if save:
            text_list.insert(0, text)

        # 只存20条
        if len(text_list) >= 20:
            text_list = text_list[:20]

        glob.set_gl_input_list(text_list)
        config_set({"cache": {"input_histroy": text_list}})

    def click_to_input(self, event):
        # 输入历史 - 双击再次输入
        item = self.input_histroy.identify('item', event.x, event.y)
        if not item:
            return
        text = self.input_histroy.item(item)['text']
        self.devices_manager(name=[self.input_task, text, "输入字符"])

    # 右键删除
    def show_context_menu(self, event):
        # 输入历史 - 右击条目展示菜单栏
        selected_item = self.input_histroy.identify_row(event.y)
        if not selected_item:
            return
        self.input_histroy.selection_set(selected_item)  # 自动选中当前条目
        self.input_histroy_menu.post(event.x_root, event.y_root)

    def delete_selected_item(self):
        # 输入历史 - 删除选中的条目
        cur_item = self.input_histroy.selection()[0]
        text = self.input_histroy.item(cur_item)['text']
        self.input_histroy_list(text=text, save=False)
        self.input_histroy.delete(cur_item)

    def input_captcha_no(self, domain_name=""):
        # 输入验证码
        cur_item = self.input_histroy.focus()
        if not cur_item:
            return
        self.input_CaptchaNo_label.config(text="发送中...")
        text = self.input_histroy.item(cur_item)['text']
        host = "https://udb.babybus.com" if not domain_name == "test" else "https://udb.development.platform.babybus.com"
        url = host + "/AppSync/GetPhoneCaptcha?Phone=" + text + "&AccountGroupID=1"

        try:
            response = requests.request("GET", url)
            res = json.loads(response.text)
        except:
            res = {"ResultCode": -1}
        if res["ResultCode"] == "0":
            self.devices_manager(name=[self.input_task, res["Data"]['CaptchaNo'], "输入字符"])
            self.input_CaptchaNo_label.config(text="已输入：" + res["Data"]['CaptchaNo'])
        else:
            self.input_CaptchaNo_label.config(text="失败" + text)

    # ===========WiFi代理的方法
    def wifi_proxy_set(self, device, status):
        """
        设置全局WiFi代理
        :param device: 设备
        :param status: 开启还是关闭
        :return: None
        """
        ip, port = (self.wifi_ip_entry.get(), self.wifi_port_entry.get()) if status else ("", "0")

        if status:
            ip_history_list = glob.get_gl_ip_history()
            ip, port = self.wifi_ip_entry.get(), self.wifi_port_entry.get()
            if ip in ip_history_list:
                ip_history.remove(ip)
            ip_history_list.insert(0, ip)
            config_set({"cache": {"ip_history": ip_history_list}})
            glob.set_gl_ip_history(ip_history_list)
            self.wifi_ip_entry["value"] = ip_history_list

        if wifi_proxy_setting(device, ip, port, status):
            self.devices_checkbutton()  # 刷新设备复选框

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
        for i in glob.get_gl_task_list():
            # 只更新没有更新过的数据
            if i["序号"] > int(first_id):
                item_id = self.tree.insert("", 0, text=i["序号"],
                                           values=(i['状态'], i['设备'], i['文件名'], i['app_id']))
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
            self.thread_it(self.open_task, task['设备ID'], task)
        elif commend_tpye == "clone":
            self.thread_it(self.clone_task, task)
        elif commend_tpye == "log":
            if task["日志"]:
                show_log(task)
            else:
                self.massage_label.config(text="日志为空")
        elif commend_tpye == "set_app_key":
            self.app_key_setting(new_app_key=task["app_id"])

    def app_key_select(self, eventObject):
        # 包名下拉框选择事件
        self.app_key_setting(self.app_key_entry.get())

    def app_key_setting(self, new_app_key):
        key_histroy = glob.get_gl_app_key_histroy()

        # 保存新包名
        self.app_key_var.set(new_app_key)
        config_set({"app": {"app_key": new_app_key}})

        # 顺序换到首个
        if new_app_key in key_histroy:
            key_histroy.remove(new_app_key)
        key_histroy.insert(0, new_app_key)

        # 只存10条包名历史
        if len(key_histroy) >= 10:
            key_histroy = key_histroy[:10]
        self.app_key_entry['values'] = key_histroy

        config_set({"app": {"app_key_histroy": key_histroy}})

        glob.set_gl_app_key_histroy(key_histroy)
        glob.set_gl_app_key(new_app_key)
        self.massage_label.config(text="已设置包名" + new_app_key)

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
        """
        构建复选框
        :return:
        """
        # 用于保存勾选状态
        select_devices = [self.devices[i][0] for i in self.checkboxes if self.checkboxes[i].get()]

        # 清除现有的复选按钮
        for check_btn in self.devices_button:
            check_btn.destroy()
        self.devices_button.clear()

        # 更新设备和全局设备
        self.checkboxes = {}
        self.devices = get_devices_all()
        glob.set_gl_devices(self.devices)

        if not self.devices:
            c = Checkbutton(self.devices_checkFrame, text="无设备连接", state='disabled', width=60)
            c.grid(row=1, column=0)
            self.devices_button.append(c)
        else:
            width = int(60 / len(self.devices))
            for i, device in enumerate(self.devices):
                wifi_proxy = "【已代理】" if wifi_proxy_check(device[0])["state"] else ""
                self.checkboxes[i] = BooleanVar(value=device[0] in select_devices)
                c = Checkbutton(self.devices_checkFrame, text=device[1] + wifi_proxy, variable=self.checkboxes[i],
                                width=width)
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
            return devices_all
        return select_devices

    def devices_manager(self, name):
        # 需要使用到设备的方法，都先判断一遍是否有选中的设备
        select_devices = self.devices_checkbutton_get()
        if not select_devices:
            self.massage_label.config(text="没有选中设备")
            return
        # name = [方法名，参数，任务状态] ，现在是list，后面优化成字典
        if isinstance(name, list):
            # 通用流程
            for d in select_devices:
                self.thread_it(name[0], d, name[1])
                task_control(device=d, status=name[2])
            return
        for d in select_devices:
            # 特殊流程
            if name == "delete":
                self.thread_it(self.delete_task, d, glob.get_gl_app_key())
            elif name == "open":
                self.thread_it(self.open_task, d)

    def delete_task(self, device, app_id):
        # 卸载任务管理
        packages = get_packages_list(device)
        if app_id not in packages:
            task_control(app_id=app_key, device=device, status="设备上无包")
            return

        task_id = task_control(app_id=app_id, device=device, status="卸载中")
        result = uninstall(device, app_id)
        item_id = self.get_task(task_id)["item_id"]
        if result:
            task_control(task_id=task_id, app_id=app_id, device=device, status="卸载成功")
            self.set_state_tree(item_id, "卸载成功")
        else:
            task_control(task_id=task_id, app_id=app_id, device=device, status="卸载失败")
            self.set_state_tree(item_id, "卸载失败")

    def input_task(self, device, text):
        # 输入字符串 任务管理
        if not text:
            text = self.input_var.get()
            self.input_histroy_list(text=text)
        input_text(device, text)

    def open_task(self, device, task=None):
        # 打开流程，包含启动时常日志处理
        if task:
            app_id = task['app_id']
        else:
            app_id = self.app_key_entry.get()
        info = open_app(device, app_id)
        task_control(device=device, app_id=app_id, status="打开应用", log=info)

    @staticmethod
    def get_task(task_id):
        # 获取任务详情
        for i in glob.get_gl_task_list():
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
                task_control(task_id=task_id, path=f, device="", status="核验包成功", log=result)
                self.set_state_tree(item_id, "核验包成功")
            elif result["总状态"]["state"] == -1:
                task_control(task_id=task_id, path=f, device="", status="核验包失败", log=result)
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
                task_control(path=path, device=device, status="安装成功", app_id=appkey_list[0], task_id=task_id)
                self.set_state_tree(item_id, "安装成功")
                if is_luncher:
                    appkey = appkey_list[0][0]
                    luncher_app(device, appkey)
            else:
                task_control(path=path, device=device, status="安装失败", task_id=task_id)
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


if __name__ == '__main__':
    init_window = Tk()  # 实例化出一个父窗口
    InstallApp(init_window)
    init_window.mainloop()
