import collections
from tkinter import scrolledtext
import requests
import json
import time
import logging
import tkinter as tk
import threading
from tkinter import *
import re

# 设置日志格式
logging.basicConfig(level=logging.INFO, format='')


class LogViewer:
    def __init__(self, log_frame):
        self.log_frame = log_frame
        self.log_frame.title("日志展示框")
        self.width = 1280
        self.height = 720
        self.log_frame.geometry(f"{self.width}x{self.height}")

        # 创建日志代理的框架
        self.log_proxy_frame = Frame(self.log_frame)
        self.log_proxy_frame.grid(row=0, column=0, sticky="w")

        # 按钮启动日志获取
        self.search_label = Label(self.log_proxy_frame, text="请输入IP地址：")
        self.search_label.grid(row=0, column=0, sticky="w", padx=2)

        # IP地址输入框
        self.ip_var = StringVar()
        self.ip_var.set("10.8.26.222")
        self.ip = Entry(self.log_proxy_frame, textvariable=self.ip_var, width=11)
        self.ip.grid(row=0, column=1)

        # 连接标签
        self.connect_label = Label(self.log_proxy_frame, text=":")
        self.connect_label.grid(row=0, column=2, sticky="w", padx=1)

        # 设置ip端口
        self.ip_port_var = StringVar()
        self.ip_port_var.set("8888")
        self.ip = Entry(self.log_proxy_frame, textvariable=self.ip_port_var, width=5)
        self.ip.grid(row=0, column=3)

        # 开始按钮
        self.file_app_button = tk.Button(self.log_proxy_frame, text="开始", width=8, command=self.start_logging)
        self.file_app_button.grid(row=0, column=4, sticky="w", padx=2)

        # 停止按钮
        self.stop_button = tk.Button(self.log_proxy_frame, text="停止", width=8, command=self.stop_logging)
        self.stop_button.grid(row=0, column=5, sticky="w", padx=2)

        # 创建清除按钮
        self.clear_button = tk.Button(self.log_proxy_frame, text="清除", width=8, command=self.clear_logs)
        self.clear_button.grid(row=0, column=6, sticky="w", padx=2)

        # 创建滚动底部按钮
        self.clear_button = tk.Button(self.log_proxy_frame, text="滚动底部", width=8, command=self.scroll_to_bottom)
        self.clear_button.grid(row=0, column=7, sticky="w", padx=2)

        # 提示标签
        self.sconvenient_label = Label(self.log_proxy_frame, text="日志类型过滤：")
        self.sconvenient_label.grid(row=0, column=8, sticky="w", padx=2)

        # 输入框用于类型搜索
        self.type_entry = tk.Entry(self.log_proxy_frame, width=18)
        self.type_entry.grid(row=0, column=9, sticky="W")

        # 搜索按钮
        self.type_button = tk.Button(self.log_proxy_frame, text="搜索", width=8,
                                     command=lambda: self.filter_logs("", "custom_type"))
        self.type_button.grid(row=0, column=10, sticky="W", padx=2)

        # 排除按钮
        self.type_button = tk.Button(self.log_proxy_frame, text="排除", width=8, command=self.highlight_keyword)
        self.type_button.grid(row=0, column=11, sticky="W", padx=2)

        self.type_keywords = {"埋点": ["平台统计", "经分"], "数学调试": ["数学调试事件"], "全部": ["ALL"]}
        self.type_keys = ""
        for idx, keyword in enumerate(self.type_keywords):
            btn = tk.Button(
                self.log_proxy_frame,
                text=keyword,  # 这里直接key键作为按钮文本
                width=10,
                command=lambda k=keyword: self.filter_logs(k, "type")
            )
            btn.grid(row=0, column=12 + idx, sticky="W", padx=2)

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

        # 创建日志代理的框架
        self.log_keyword_frame = Frame(self.log_frame)
        self.log_keyword_frame.grid(row=1, column=0, sticky="w")
        # 提示标签
        self.search_label1 = Label(self.log_keyword_frame, text=" 请输入关键词：")
        self.search_label1.grid(row=0, column=0, sticky="w")

        # 输入框用于关键词搜索
        self.search_entry = tk.Entry(self.log_keyword_frame, width=18)
        self.search_entry.grid(row=0, column=1, sticky="W")

        # 搜索按钮
        self.search_button = tk.Button(self.log_keyword_frame, text="搜索", width=8, command=self.highlight_keyword)
        self.search_button.grid(row=0, column=2, sticky="W", padx=2)

        # 创建过滤按钮
        self.filter_button = tk.Button(self.log_keyword_frame, text="过滤", width=8, command=self.filter_keywords)
        self.filter_button.grid(row=0, column=3, sticky="W", padx=2)

        # 创建上下按钮
        self.prev_button = Button(self.log_keyword_frame, text="上一个", width=8, command=self.show_prev)
        self.prev_button.grid(row=0, column=4, sticky="W", padx=2)

        self.next_button = Button(self.log_keyword_frame, text="下一个", width=8, command=self.show_next)
        self.next_button.grid(row=0, column=5, sticky="W", padx=2)

        # 显示结果数的标签
        self.result_count_label = Label(self.log_keyword_frame, text="当前未搜索")
        self.result_count_label.grid(row=0, column=6, sticky="W")  # 添加适当的左边距

        # 创建日志过滤的框架
        self.log_view_frame = Frame(self.log_frame)
        self.log_view_frame.grid(row=2, column=0, sticky="w")
        # 创建滚动文本区域用于显示日志
        self.log_text = scrolledtext.ScrolledText(self.log_view_frame, width=157, height=34,
                                                  font=('Microsoft YaHei', 10))
        self.log_text.grid(row=3, column=0)

        # 监视
        self.log_text.bind('<MouseWheel>', self.on_mouse_scroll)
        self.log_text.bind('<Key>', self.on_key_scroll)

    def start_logging(self):
        """启动日志获取线程"""
        if not self.logging_switch:  # 如果当前没有进行日志获取，则开始新的线程
            self.logging_switch = True
            threading.Thread(target=self.run, daemon=True).start()

    def stop_logging(self):
        """停止日志获取"""
        self.logging_switch = False  # 设置标志为False以停止日志获取

    def clear_logs(self):
        """清除日志文本框中的内容"""
        self.log_list = collections.deque([])  # 清除列表
        self.log_text.delete(1.0, END)


    def run(self):
        """获取日志的方法"""
        ip_address = self.ip_var.get()
        ip_port = self.ip_port_var.get()
        full_address = f"{ip_address}:{ip_port}"  # 连接IP与端口
        while self.logging_switch:
            log_list = self.get_log(full_address)
            if log_list == -1:
                self.log_to_text(time.strftime("%Y-%m-%d %H:%M:%S") + " 【异常】应用未启动，或日志开关未开启")
            else:
                for log_entry in reversed(log_list):  # 倒序读取日志列表
                    self.print_log(log_entry)
                    self.timeStamp = log_entry.get("timeStamp", self.timeStamp)
                if self.auto_scroll:
                    self.log_text.yview(tk.END)  # 自动滚动到底部
            time.sleep(1)  # 暂停一秒

    def get_log(self, ip):
        """从指定 URL 获取日志"""
        url = "http://" + ip + "/logs"
        body = {"timeStamp": str(self.timeStamp)}
        try:
            response = requests.post(url, json=body)
            res = json.loads(response.text)
            return res.get("logs", [])
        except Exception as e:
            logging.error(f"获取日志失败: {e}")
            return -1

    def print_log(self, text):
        """打印日志到文本框"""
        if "BBRest" != text['logType'] and "BBThirdAD" != text['logType']:
            log_message = f"{text['time']} 【{text['logType']}】：{text['message'].strip()}"
            self.log_list.append(log_message)  # 将日志信息存入列表

            # 如果当前是过滤状态, 判断日志是否包含关键词
            if self.key_filtering:
                keyword = self.search_entry.get().strip().lower()
                if keyword in log_message.lower():
                    self.log_to_text(log_message)  # 输出到文本框
            # 如果当前是过滤状态, 判断日志是否包含类型
            elif self.type_filtering:  # 类型过滤
                if any(type_value in text['logType'] for type_value in self.type_keywords[self.type_keys]):
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
            types_to_match = self.type_keywords[self.type_keys]  # 获取对应的类型列表
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
        self.log_text.yview(tk.END)  # 自动滚动到底部

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
                self.current_result_index = 0  # 设置当前索引为第一个结果
                self.highlight_current_result()  # 高亮当前结果
                self.result_count_label.config(text=f"共找到 1/{self.count} 条")  # 更新结果显示
            else:
                self.current_result_index = -1  # 表示没有结果
                self.result_count_label.config(text="未找到结果")

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
        self.auto_scroll = True
        self.log_text.yview(tk.END)

    def on_mouse_scroll(self, event):
        """当用户使用鼠标滚动时，设置不再自动滚动"""
        self.auto_scroll = False

    def on_key_scroll(self, event):
        """当用户使用键盘滚动时，设置不再自动滚动"""
        self.auto_scroll = False


def thread_it(func, *args):
    """将函数打包进线程"""
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)  # 设置为守护线程
    t.start()


if __name__ == '__main__':
    root = tk.Tk()
    app = LogViewer(root)
    root.mainloop()
