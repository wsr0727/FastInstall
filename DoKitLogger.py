import collections
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import tkinter as tk
import threading
import re
import urllib.request
import gzip
import urllib.error
import time
from PIL import Image, ImageTk
import io
from datetime import datetime
from Glob import *
from Cache import *
import requests

# 打包指令 pyinstaller -F -w DoKitLogger.py

ip_port_history = get_cache()[4]  # 初始化缓存
glob.set_gl_ip_port_history(ip_port_history)


class LogViewer:
    def __init__(self, log_bigframe):
        self.log_bigframe = log_bigframe
        self.width = 1340
        self.height = 750
        self.log_bigframe.title("iOS测试工具")
        self.log_bigframe.geometry(f"{self.width}x{self.height}")
        self.log_frame = tk.Frame(self.log_bigframe)
        self.log_frame.grid(row=0, column=0, sticky="w")
        # 创建日志代理的框架
        self.log_proxy_frame = tk.Frame(self.log_frame)
        self.log_proxy_frame.grid(row=0, column=0, sticky="w")

        # 按钮启动日志获取
        self.search_label = tk.Label(self.log_proxy_frame, text="请输入IP地址：")
        self.search_label.grid(row=0, column=0, sticky="w", padx=2)

        # ip下拉框
        self.ip_var = tk.StringVar()
        ip_port_dict = glob.get_gl_ip_port_history()
        first_value = ""
        if ip_port_dict:
            # 获取字典中的第一个键（Key），即第一个 IP 地址
            first_ip = next(iter(ip_port_dict))
            first_value = ip_port_dict[first_ip]
            self.ip_var.set(first_ip)  # 设置默认值为第一个历史 IP
        key_list = list(ip_port_dict.keys())

        # 创建下拉框（Combobox）以选择 IP 地址
        self.ip_var_entry = ttk.Combobox(self.log_proxy_frame, textvariable=self.ip_var, width=15,
                                         values=[f"{key} - {ip_port_dict[key]}" for key in ip_port_dict.keys()])
        self.ip_var_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ip_var_entry.bind("<<ComboboxSelected>>", self.update_device_notes)

        # 连接标签
        self.connect_label = tk.Label(self.log_proxy_frame, text=":")
        self.connect_label.grid(row=0, column=2, sticky="w", padx=1)

        # 设置ip端口
        self.ip_port_var = tk.StringVar()
        self.ip_port_var.set("7777")
        self.ip = tk.Entry(self.log_proxy_frame, textvariable=self.ip_port_var, width=5)
        self.ip.grid(row=0, column=3)

        # 设置设备备注
        self.device_notes = tk.StringVar()
        self.device_notes.set(first_value)

        self.device_notes_entry = tk.Entry(self.log_proxy_frame, textvariable=self.device_notes, width=8)
        self.device_notes_entry.grid(row=0, column=4, padx=2, pady=2)

        # 开始按钮
        self.file_app_button = tk.Button(self.log_proxy_frame, text="开始", width=7, command=self.start_logging)
        self.file_app_button.grid(row=0, column=5, sticky="w", padx=2)

        # 停止按钮
        self.stop_button = tk.Button(self.log_proxy_frame, text="停止", width=7, command=self.stop_logging)
        self.stop_button.grid(row=0, column=6, sticky="w", padx=2)

        # 创建清除按钮
        self.clear_button = tk.Button(self.log_proxy_frame, text="清除", width=7, command=self.clear_logs)
        self.clear_button.grid(row=0, column=7, sticky="w", padx=2)

        # 创建滚动底部按钮
        self.clear_button = tk.Button(self.log_proxy_frame, text="滚动底部 (✔)", width=11,
                                      command=self.scroll_to_bottom)
        self.clear_button.grid(row=0, column=8, padx=2, pady=2)

        # 初始化数值
        self.current_result_index = -1  # 初始化为-1，表示没有当前结果
        self.count = 0  # 初始化计数为0
        self.found_results = []  # 需要预先填充搜索结果
        self.result_count_label = None
        self.log_text = None  # 初始日志框为空
        self.logging_switch = False  # 初始化获取日志是关闭
        self.timeStamp = 0  # 用于接初始口请求时间
        self.log_list = collections.deque([])  # 用于存储日志信息
        self.key_filtering = False  # 关键词过滤-初始时不处于过滤模式
        self.type_filtering = False  # 固定类型过滤-初始时不处于过滤模式
        self.type_most_filtering = False  # 自定义类型过滤-初始时不处于过滤模式
        self.auto_scroll = True  # 默认自动定位在日志框底部
        self.unique_log_types = set()  # 存储唯一的 logType
        self.button_row = 1  # 用于创建分类按钮下标的初始值
        self.current_preview_window = None  # 初始化用于存储当前预览窗口的变量
        self.full_address = None
        #  录屏初始变量
        self.is_recording = False
        self.is_processing = False
        self.video_available = False
        self.current_video_filename = "record.mp4"

        # 创建日志代理的框架
        self.log_keyword_frame = tk.Frame(self.log_frame)
        self.log_keyword_frame.grid(row=1, column=0, sticky="w")
        # 提示标签
        self.search_label1 = tk.Label(self.log_proxy_frame, text=" 请输入关键词：")
        self.search_label1.grid(row=0, column=9, sticky="w", padx=2)

        # 输入框用于关键词搜索
        self.search_entry = tk.Entry(self.log_proxy_frame, width=18)
        self.search_entry.grid(row=0, column=10, sticky="W")

        # 搜索按钮
        self.search_button = tk.Button(self.log_proxy_frame, text="搜索", width=7, command=self.highlight_keyword)
        self.search_button.grid(row=0, column=11, sticky="W", padx=2)

        # 创建过滤按钮
        self.filter_button = tk.Button(self.log_proxy_frame, text="过滤", width=7, command=self.filter_keywords)
        self.filter_button.grid(row=0, column=12, sticky="W", padx=2)

        # 创建上下按钮
        self.prev_button = tk.Button(self.log_proxy_frame, text="上一个", width=7, command=self.show_prev)
        self.prev_button.grid(row=0, column=13, sticky="W", padx=2)

        self.next_button = tk.Button(self.log_proxy_frame, text="下一个", width=7, command=self.show_next)
        self.next_button.grid(row=0, column=14, sticky="W", padx=2)

        # 显示结果数的标签
        self.result_count_label = tk.Label(self.log_proxy_frame, text="当前未搜索")
        self.result_count_label.grid(row=0, column=15, sticky="W")  # 添加适当的左边距

        # 影像模块 录屏与图片
        self.image_frame = tk.Frame(self.log_frame)
        self.image_frame.grid(row=1, column=0, sticky="W")

        # 录屏
        self.image_label = tk.Label(self.image_frame, text="iOS录屏功能： ")
        self.image_label.grid(row=0, column=0, sticky="w", padx=2)

        self.start_btn = tk.Button(self.image_frame, text="▶ 开始录制",
                                   command=self.start_recording,
                                   bg='#27ae60', fg='white', width=10)
        self.start_btn.grid(row=0, column=1, padx=5, pady=5)

        self.stop_btn = tk.Button(self.image_frame, text="■ 停止录制",
                                  command=self.stop_recording,
                                  fg='white', width=10,
                                  state='disabled')
        self.stop_btn.grid(row=0, column=2, padx=5, pady=5)

        self.download_btn = tk.Button(self.image_frame, text="⬇ 下载视频",
                                      command=self.download_video,
                                      fg='white', width=10,
                                      state='disabled')
        self.download_btn.grid(row=0, column=3, padx=5, pady=5)

        # 截图
        # self.image_label = tk.Label(self.image_frame, text="截图功能：")
        # self.image_label.grid(row=0, column=4, sticky="w", padx=2)

        self.next_button = tk.Button(self.image_frame, text="截图", width=7, command=self.get_screenshot)
        self.next_button.grid(row=0, column=4, sticky="W", padx=5)

        self.log_under_frame = tk.Frame(self.log_bigframe)
        self.log_under_frame.grid(row=2, column=0, sticky="W")

        # 提示标签
        self.search_title_label = tk.Label(self.log_under_frame, text="日志类型")
        self.search_title_label.grid(row=0, column=0, sticky="w")

        #  创建tag选择按钮
        self.log_tag_frame = tk.Frame(self.log_under_frame)
        self.log_tag_frame.grid(row=1, column=0, sticky="w")

        # 创建日志过滤的框架
        self.log_view_frame = tk.Frame(self.log_under_frame)
        self.log_view_frame.grid(row=1, column=1, sticky="w")
        # 创建滚动文本区域用于显示日志
        self.log_text = scrolledtext.ScrolledText(self.log_view_frame, width=150, height=34,
                                                  font=('Microsoft YaHei', 10))

        self.log_text.grid(row=0, column=0)

        # 监视
        self.log_text.bind('<MouseWheel>', self.on_mouse_scroll)
        self.log_text.bind('<Key>', self.on_key_scroll)
        self.log_text.bind("<Visibility>", self.check_scroll_position)  # 监控可见性变化
        self.log_text.bind("<ButtonPress-1>", self.on_mouse_press)  # 绑定鼠标按下事件

    def start_logging(self):
        """启动日志获取线程"""
        if self.logging_switch:  # 如果已经在运行，先停止
            self.logging_switch = False
            time.sleep(1)  # 等待线程结束
        self.logging_switch = True
        ip_address = self.ip_var.get()
        device = self.device_notes.get()
        self.update_ip_history(ip_address, device)
        threading.Thread(target=self.run, daemon=True).start()

    def stop_logging(self):
        """停止日志获取"""
        self.logging_switch = False  # 设置标志为False以停止日志获取

    def clear_logs(self):
        """清除日志文本框中的内容"""
        self.log_list = collections.deque([])  # 清除列表
        self.log_text.delete(1.0, tk.END)

    def run(self):
        """获取日志的方法"""
        ip_address = self.ip_var.get()
        ip_port = self.ip_port_var.get()
        self.full_address = f"{ip_address}:{ip_port}"  # 连接IP与端口
        self.timeStamp = int(time.time() * 1000)  # 设置为当前时间戳，单位为毫秒
        last_processed_time = self.timeStamp  # 记录上次处理的时间戳
        # self.update_ip_history(ip_address)
        while self.logging_switch:
            log_list = self.get_log(self.full_address)
            if log_list == -1:
                self.log_to_text(time.strftime("%Y-%m-%d %H:%M:%S") + " 【异常】应用未启动，或日志开关未开启")
            else:
                for log_entry in reversed(log_list):  # 倒序读取日志列表
                    log_time = log_entry.get("timeStamp")  # 获取当前日志的时间戳
                    if log_time > last_processed_time:  # 只处理新日志
                        self.print_log(log_entry)
                        last_processed_time = log_time  # 更新最后处理的时间戳
                if self.auto_scroll:
                    self.log_text.yview(tk.END)  # 自动滚动到底部
            time.sleep(1)  # 暂停一秒

    def get_log(self, ip):
        url = f"http://{ip}/logs"
        body = {"timeStamp": str(self.timeStamp)}
        data = json.dumps(body).encode('utf-8')

        try:
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_data = response.read()

                # 检查是否被 Gzip 压缩 (判断前两个字节是否为 0x1f 0x8b)
                if raw_data[:2] == b'\x1f\x8b':
                    raw_data = gzip.decompress(raw_data)

                # 解码为字符串
                res_text = raw_data.decode('utf-8')
                res = json.loads(res_text)
                return res.get("logs", [])
        except Exception as e:
            logging.error(f"获取日志失败: {e}")
            return []

    def print_log(self, text):
        """打印日志到文本框"""
        if "BBRest" != text['logType'] and "BBThirdAD" != text['logType']:
            log_message = f"{text['time']} 【{text['logType']}】：{text['message'].strip()}"
            self.log_list.append(log_message)  # 将日志信息存入列表
            if text['logType'] not in self.unique_log_types:
                self.unique_log_types.add(text['logType'])
                self.add_log_type_button(text['logType'])
            # 如果当前是过滤状态, 判断日志是否包含关键词
            if self.key_filtering:
                keyword = self.search_entry.get().strip().lower()
                if keyword in log_message.lower():
                    self.log_to_text(log_message)  # 输出到文本框
            # 如果当前是过滤状态, 判断日志是否包含类型
            elif self.type_filtering:  # 类型过滤
                if any(type_value in text['logType'] for type_value in self.type_keys):
                    self.log_to_text(log_message)
            elif self.type_most_filtering:
                input_text = self.type_entry.get()
                types_to_match = [item.strip() for item in input_text.split(',')]
                if any(type_value in text['logType'] for type_value in types_to_match):
                    self.log_to_text(log_message)
            else:
                self.log_to_text(log_message)  # 输出到文本框

    def filter_keywords(self):
        """根据输入的关键词过滤日志"""
        keyword = self.search_entry.get().strip().lower()
        self.key_filtering = True  # 进入关键词过滤模式
        self.type_filtering = False
        self.type_most_filtering = False
        self.log_text.delete(1.0, tk.END)  # 清除当前文本
        for log_message in self.log_list:
            if keyword in log_message.lower():  # 检查关键词
                self.log_text.insert(tk.END, log_message + '\n')
        if self.auto_scroll:
            self.log_text.yview(tk.END)  # 自动滚动到底部

    def filter_logs(self, keyword, filter_type):
        """根据输入的固定或自定义类型过滤日志"""
        self.log_text.delete(1.0, tk.END)  # 清除当前文本
        types_to_match = []
        if filter_type == "type":
            self.type_keys = keyword
            self.key_filtering = False  # 关闭关键词过滤模式
            self.type_filtering = True  # 开启固定类型过滤模式
            self.type_most_filtering = False  # 关闭自定义类型过滤模式
            types_to_match = self.type_keys  # 获取对应的类型列表
        elif filter_type == "custom_type":
            self.key_filtering = False  # 关闭关键词过滤模式
            self.type_filtering = False  # 关闭固定类型过滤模式
            self.type_most_filtering = True  # 开启自定义类型过滤模式
            input_text = self.type_entry.get()
            types_to_match = [item.strip() for item in input_text.split('，')]
        if keyword != "全部":
            for log_message in self.log_list:
                # 使用正则表达式提取【】内的字段
                match = re.search(r'【(.*?)】', log_message)
                if match:  # 如果匹配成功
                    extracted_field = match.group(1)  # 获取匹配的内容
                    # 判断提取的字段是否包含在 types_to_match 列表中
                    if any(type_value in extracted_field for type_value in types_to_match):
                        self.log_text.insert(tk.END, log_message + '\n')

        else:
            # 全部日志输出
            self.key_filtering = False  # 关闭关键词过滤模式
            self.type_filtering = False  # 关闭固定类型过滤模式
            self.type_most_filtering = False  # 关闭自定义类型过滤
            for log_message in self.log_list:
                self.log_text.insert(tk.END, log_message + '\n')
        if self.auto_scroll:
            self.log_text.yview(tk.END)  # 自动滚动到底部

    def add_log_type_button(self, log_type):
        """为新的 logType 添加按钮"""
        button = tk.Button(self.log_tag_frame, text="全部",
                           command=lambda lt=log_type: self.filter_logs("全部", "type"),
                           width=15)
        button.grid(row=0, column=0, sticky="w")  # 在指定的行添加按钮
        button = tk.Button(self.log_tag_frame, text=log_type, command=lambda lt=log_type: self.filter_logs(lt, "type"),
                           width=15)
        button.grid(row=self.button_row, column=0, sticky="w")  # 在指定的行添加按钮
        self.button_row += 1  # 增加行数计数器

    def sanitize_message(self, message):
        """过滤掉无法显示的字符，只保留可显示的 Unicode 字符。"""
        return ''.join(c for c in message if ord(c) <= 0xFFFF)

    def log_to_text(self, message):
        """将日志输出到文本区域"""
        try:
            sanitized_message = self.sanitize_message(message)
            self.log_text.insert(tk.END, sanitized_message + '\n')
        except Exception as e:
            logging.error(f"错误日志：'{message}'")  # 记录出错信息和导致错误的消息

    def highlight_keyword(self):
        """高亮显示输入的关键词，并更新结果计数"""
        self.auto_scroll = False
        self.update_button()
        keyword = self.search_entry.get()
        self.log_text.tag_remove('highlight', '1.0', tk.END)  # 清除之前的黄色高亮
        self.log_text.tag_remove('current_highlight', '1.0', tk.END)  # 清除之前的蓝色高亮
        self.found_results.clear()  # 清除之前的结果
        self.count = 0  # 初始化为0

        if keyword:
            start_idx = '1.0'
            while True:
                start_idx = self.log_text.search(keyword, start_idx, stopindex=tk.END)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(keyword)}c"
                self.log_text.tag_add('highlight', start_idx, end_idx)  # 高亮匹配的关键词
                self.found_results.append(start_idx)  # 保存找到的起始索引
                start_idx = end_idx

            self.log_text.tag_config('highlight', background='yellow')  # 设置高亮颜色

            # 更新计数
            self.count = len(self.found_results)
            if self.count > 0:
                self.current_result_index = self.count - 1  # 设置当前索引为第一个结果
                self.highlight_current_result()  # 高亮当前结果
                self.result_count_label.config(text=f"共找到 {self.count}/{self.count} 条")  # 更新结果显示
            else:
                self.current_result_index = -1  # 表示没有结果
                self.result_count_label.config(text="未找到结果")
            # time.sleep(1)
            # self.highlight_keyword()

    def show_next(self):
        """显示下一个搜索结果"""
        if self.found_results:
            self.current_result_index += 1
            if self.current_result_index >= self.count:
                self.current_result_index = 0  # 回绕到第一个
            self.highlight_current_result()  # 高亮当前结果
            self.result_count_label.config(text=f"共找到 {self.current_result_index + 1}/{self.count} 条")

    def show_prev(self):
        """显示上一个搜索结果"""
        if self.found_results:
            self.current_result_index -= 1
            if self.current_result_index < 0:
                self.current_result_index = self.count - 1  # 回绕到最后一个
            self.highlight_current_result()  # 高亮当前结果
            self.result_count_label.config(text=f"共找到 {self.current_result_index + 1}/{self.count} 条")

    def highlight_current_result(self):
        """高亮当前结果并滚动到视图中"""
        for idx in range(len(self.found_results)):
            self.log_text.tag_remove('current_highlight', self.found_results[idx],
                                     f"{self.found_results[idx]}+{len(self.search_entry.get())}c")

        if self.found_results and self.current_result_index >= 0:
            current_result = self.found_results[self.current_result_index]
            self.log_text.tag_add('current_highlight', current_result,
                                  f"{current_result}+{len(self.search_entry.get())}c")
            self.log_text.tag_config('current_highlight', background='skyblue')
            self.log_text.see(current_result)  # 滚动文本框以使当前结果可见

    def scroll_to_bottom(self):
        """点击按钮滚动到底部"""
        self.auto_scroll = not self.auto_scroll
        self.update_button()

        if self.auto_scroll:
            self.log_text.yview(tk.END)

    def update_button(self):
        """更新按钮文本和样式"""
        if self.auto_scroll:
            self.clear_button.config(text="滚动底部 (✔)", bg="#27ae60")
        else:
            self.clear_button.config(text="滚动底部 (✖)", bg="#e74c3c")

    def on_mouse_scroll(self, event):
        """当用户使用鼠标滚动时，设置不再自动滚动"""
        self.auto_scroll = False
        self.check_scroll_position()

    def on_key_scroll(self, event):
        """当用户使用键盘滚动时，设置不再自动滚动"""
        self.auto_scroll = False
        self.check_scroll_position()

    def on_mouse_press(self, event):
        """当用户按下鼠标时，设置自动滚动为 False"""
        self.auto_scroll = False
        self.check_scroll_position()

    def check_scroll_position(self, event=None):
        """检查文本框是否滚动到最底部"""
        # 获取当前视图和文本框的总高度
        current_view = self.log_text.yview()
        # 判断是否滚动到最底部
        if current_view[1] >= 1.0:  # 如果视图的结束位置在1.0或更高，表示已到达底部
            self.auto_scroll = True
        else:
            self.auto_scroll = False
        self.update_button()  # 更新按钮状态

    #  截图相关函数
    def get_screenshot(self):
        ip_address = self.ip_var.get()
        ip_port = self.ip_port_var.get()
        self.full_address = f"{ip_address}:{ip_port}"

        current_timestamp = int(time.time() * 1000)
        url = f"http://{self.full_address}/screenshot?scale=0.7&format=jpeg&t={current_timestamp}"

        try:
            # 发送 GET 请求
            with urllib.request.urlopen(url, timeout=5) as response:
                # 检查状态码 (urlopen 在非 2xx 时通常会抛出 HTTPError，但显式检查更稳妥)
                if response.status != 200:
                    raise Exception(f"HTTP Status: {response.status}")

                # 获取二进制图像数据
                img_data = response.read()

                # 直接展示图片
                self.show_image_in_new_window(img_data)

        except urllib.error.HTTPError as http_err:
            self.log_to_text(f"HTTP 错误: {http_err}")
        except urllib.error.URLError:
            self.log_to_text(f"连接错误: 无法连接到 {self.full_address}")
        except Exception as e:
            self.log_to_text(f"获取数据失败: {e}")
            return -1

    def show_image_in_new_window(self, image_data):
        """
        在新弹出的 Tkinter 窗口中展示图片
        - 长宽比 > 1.5 (手机类): 固定宽度 1300
        - 长宽比 <= 1.5 (平板类): 固定宽度 1000
        高度按比例自动调整
        :param image_data: 图片的二进制数据 (bytes)，支持 Gzip 压缩数据
        """
        try:
            #  关闭上一个窗口
            if hasattr(self, 'current_preview_window') and self.current_preview_window is not None:
                try:
                    # 检查窗口是否仍然有效（未被手动关闭）
                    if self.current_preview_window.winfo_exists():
                        self.current_preview_window.destroy()
                except Exception:
                    pass  # 如果窗口已经不存在或出错，忽略并继续
                finally:
                    self.current_preview_window = None

            # 检测并处理 Gzip 压缩数据
            if image_data.startswith(b'\x1f\x8b'):
                try:
                    image_data = gzip.decompress(image_data)
                except Exception as decompress_err:
                    self.log_to_text(f"Gzip 解压失败: {decompress_err}")
                    return

            # 1. 从二进制数据加载 PIL 图像
            pil_image = Image.open(io.BytesIO(image_data))

            # 2. 获取原始尺寸并计算长宽比
            original_width, original_height = pil_image.size

            if original_width == 0 or original_height == 0:
                self.log_to_text("图片尺寸无效，无法展示")
                return

            aspect_ratio = original_width / original_height

            # 3. 根据长宽比决定目标宽度
            if aspect_ratio > 1.5:
                target_width = 1300
                device_type = "手机模式"
            else:
                target_width = 1000
                device_type = "平板模式"

            # 4. 计算按比例缩放后的高度
            target_height = int(original_height * (target_width / original_width))

            if target_height < 1:
                target_height = 1

            # 5. 执行缩放
            resized_pil_image = pil_image.resize((target_width, target_height), Image.LANCZOS)

            # 6. 创建一个新的顶层窗口
            new_window = tk.Toplevel(self.log_bigframe)
            new_window.title(f"实时截图预览 [{device_type}] ({target_width}x{target_height})")

            # 7. 转换图像格式
            tk_image = ImageTk.PhotoImage(resized_pil_image)

            # 8. 显示图片
            label = tk.Label(new_window, image=tk_image)
            label.pack()

            # 必须保留对 tk_image 的引用
            new_window.image = tk_image

            # 9. 计算屏幕居中坐标
            try:
                screen_width = self.log_bigframe.winfo_screenwidth()
                screen_height = self.log_bigframe.winfo_screenheight()
            except Exception:
                #  fallback: 尝试从根窗口获取
                root = self.log_bigframe.winfo_toplevel()
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()

            x = (screen_width - target_width) // 2
            y = (screen_height - target_height) // 2

            # 10. 设置窗口位置和大小
            new_window.geometry(f"{target_width}x{target_height}+{x}+{y}")

            # 保存当前窗口引用，以便下次关闭
            self.current_preview_window = new_window

            self.log_to_text(f"截图已展示 [{device_type}]")

        except Exception as e:
            self.log_to_text(f"图片展示失败: {e}")
            import traceback
            traceback.print_exc()

    def update_device_notes(self, event=None):
        """根据选择的 IP 地址更新设备备注"""
        ip_port_dict = glob.get_gl_ip_port_history()

        selected_value = self.ip_var_entry.get()
        selected_key = selected_value.split(" - ")[0]  # 获取选中的key
        self.ip_var.set(selected_key)  # 更新ip_var为选中的key

        if selected_key in ip_port_dict:
            self.device_notes.set(ip_port_dict[selected_key])  # 更新设备备注
        else:
            self.device_notes.set("")  # 如果未找到，设置为空

    def update_ip_history(self, ip, device):
        """更新 IP 历史记录"""
        ip_port_history_list = glob.get_gl_ip_port_history()
        if ip in ip_port_history_list:
            del ip_port_history_list[ip]  # 如果 IP 已存在，先移除
        new_dict = {ip: device}
        new_dict.update(ip_port_history_list)
        config_set({"cache": {"ip_port_history": new_dict}})  # 假设 config_set 是保存配置的函数
        glob.set_gl_ip_port_history(new_dict)  # 更新全局 IP 历史记录
        key_list = list(new_dict.keys())
        self.ip_var_entry["values"] = [f"{key} - {new_dict[key]}" for key in new_dict.keys()]

    # 录屏相关函数
    def log_message(self, message, level="info"):
        """修正后的日志方法"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {message}\n", level)
        self.log_text.see('end')

    def update_ui_state(self):
        """更新UI状态"""
        if self.is_recording:

            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.download_btn.config(state='disabled')

        elif self.is_processing:

            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='disabled')
            self.download_btn.config(state='disabled')

        elif self.video_available:

            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.download_btn.config(state='normal')

        else:

            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.download_btn.config(state='disabled')

    def test_connection(self):
        try:
            response = requests.get(f"http://{self.full_address}/record/status", timeout=3)
            if response.status_code == 200:
                self.log_message("服务器连接正常", "success")
            else:
                self.log_message(f"服务器响应异常: HTTP {response.status_code}", "error")
        except Exception as e:
            self.log_message(f"无法连接到服务器: {str(e)}", "error")

    def start_recording(self):
        """开始录制"""
        ip_address = self.ip_var.get()
        ip_port = self.ip_port_var.get()
        self.full_address = f"{ip_address}:{ip_port}"

        def _start():
            try:
                self.log_message("正在开启录屏...", "info")
                response = requests.post(f"http://{self.full_address}/record/start", timeout=5)
                if response.status_code == 200:
                    self.is_recording = True
                    self.video_available = False
                    self.log_frame.after(0, self.update_ui_state)
                    self.log_message("录屏已开始", "success")
                    self.start_btn.config(bg="#f0f0f0")
                    self.stop_btn.config(bg="#e74c3c")
                    self.download_btn.config(bg="#f0f0f0")

                else:
                    self.log_message(f"开始录制失败: HTTP {response.status_code}", "error")

            except Exception as e:
                self.log_message(f"网络错误: {str(e)}", "error")

        threading.Thread(target=_start, daemon=True).start()

    def stop_recording(self):
        """停止录制"""

        def _stop():
            try:
                self.log_message("正在停止录屏...", "info")
                response = requests.post(f"http://{self.full_address}/record/stop", timeout=10)
                if response.status_code == 200:
                    self.is_recording = False
                    self.is_processing = True
                    self.log_frame.after(0, self.update_ui_state)
                    self.log_message("录制已停止，等待录像就绪...", "info")
                    self.poll_video_status()
                    self.start_btn.config(bg="#27ae60")
                    self.stop_btn.config(bg="#f0f0f0")
                    self.download_btn.config(bg="#3498db")
                else:
                    self.log_message(f"停止录制失败: HTTP {response.status_code}", "error")
            except Exception as e:
                self.log_message(f"网络错误: {str(e)}", "error")

        threading.Thread(target=_stop, daemon=True).start()

    def poll_video_status(self):
        """轮询视频状态"""

        def _poll():
            max_attempts = 60
            for attempt in range(max_attempts):
                try:
                    response = requests.get(f"http://{self.full_address}/record/status", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        state = data.get("state", "")
                        available = data.get("available", False)

                        # 关键修正：必须同时满足 state==ready 和 available==true
                        if state == "ready" and available:
                            self.is_processing = False
                            self.video_available = True
                            self.current_video_filename = data.get("filename", "record.mp4")
                            size_kb = data.get("size", 0) / 1024
                            self.log_message(f"录像数据已回传 ({size_kb:.1f} KB)", "success")
                            self.log_message("录像回传完毕，下载按钮已点亮", "success")
                            self.log_frame.after(0, self.update_ui_state)
                            return

                        elif state == "error":
                            self.log_message("录像生成失败", "error")
                            self.is_processing = False
                            self.log_frame.after(0, self.update_ui_state)
                            self.start_btn.config(bg="#27ae60")
                            self.stop_btn.config(bg="#f0f0f0")
                            self.download_btn.config(bg="#f0f0f0")
                            return

                    time.sleep(1)
                except Exception as e:
                    time.sleep(1)
                    continue

            self.log_message("等待录像就绪超时", "warning")
            self.is_processing = False
            self.log_frame.after(0, self.update_ui_state)

        threading.Thread(target=_poll, daemon=True).start()

    def download_video(self):
        """下载视频"""

        def _download():
            try:

                self.log_message("正在下载录像文件...", "info")

                # 使用 /record/file 接口
                download_url = f"http://{self.full_address}/record/download?"
                response = requests.get(download_url, stream=True, timeout=30)

                if response.status_code == 200:
                    # 获取文件名
                    filename = self.current_video_filename
                    if 'content-disposition' in response.headers:
                        cd = response.headers['content-disposition']
                        if 'filename=' in cd:
                            filename = cd.split('filename=')[1].strip('"')

                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".mp4",
                        initialfile=filename,
                        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
                    )

                    if save_path:
                        with open(save_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        self.log_message(f"已触发录像下载: {os.path.basename(save_path)}", "success")
                        messagebox.showinfo("下载完成", f"视频已保存到:\n{save_path}")
                else:
                    self.log_message(f"下载失败: HTTP {response.status_code}", "error")
                    if response.status_code == 404:
                        self.log_message("提示：请确认服务器端 /record/file 路由是否正确配置", "warning")

            except Exception as e:
                self.log_message(f"下载错误: {str(e)}", "error")

        threading.Thread(target=_download, daemon=True).start()


def thread_it(func, *args):
    """将函数打包进线程"""
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)  # 设置为守护线程
    t.start()


def show_ios_window(parent=None):
    ios_toplevel = tk.Toplevel(parent)
    LogViewer(ios_toplevel)


if __name__ == '__main__':
    root = tk.Tk()
    app = LogViewer(root)
    root.mainloop()
