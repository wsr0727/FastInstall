from tkinter import *
import windnd
import shutil
import hashlib
import os
from datetime import datetime
import zipfile
import time
from pathlib import Path
import threading

# 打包指令 pyinstaller -F -w LanguageChecker.py
language = {"zh": "简体", "en": "英语", "zht": "繁体", "ja": "日语", "ko": "韩语", "pt": "葡语", "ru": "俄语",
            "vi": "越南语", "th": "泰语", "ar": "阿语", "es": "西语", "fr": "法语", "id": "印尼语"}


def calculate_md5(file_path):
    """计算文件的MD5值"""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
    except FileNotFoundError:
        return None
    return hasher.hexdigest()


def zip_to_file(file_path):
    """解压文件"""
    # 创建 ZipFile 实例对象
    zip_file = zipfile.ZipFile(file_path)
    # 创建目录
    path_cache = "/lang_cache_" + str(int(time.time()))  # 解压文件存储路径
    os.mkdir(path_cache)
    # 提取 zip 文件
    try:
        zip_file.extractall(path_cache)
        # 解压resources.arsc文件时会出错，只有打包出来的文件有问题，暂时没有解决办法
    except:
        pass
    # 关闭 zip 文件
    zip_file.close()
    return path_cache


def get_files_by_modification_date(directory):
    """将文件夹中的文件按照修改时间分组"""
    files_by_date = {}

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        # 确保这是一个文件而不是文件夹
        if os.path.isfile(filepath):
            # 获取文件的修改时间
            mod_time = os.path.getmtime(filepath)
            mod_datetime = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')

            # 将文件按修改时间（精确到日）分组
            if mod_datetime not in files_by_date:
                files_by_date[mod_datetime] = []
            files_by_date[mod_datetime].append(filename)

    return files_by_date


def get_lang_path(file_path):
    """获取音频文件地址"""
    base_path = Path(file_path)

    # 使用通配符匹配路径
    matching_paths = base_path.glob('*/snd/effect')

    for path in matching_paths:
        if path.is_dir():
            return path


def get_all_subfolders(directory):
    """返回文件夹下所有的子文件夹路径"""
    subfolders = []
    for root, dirs, _ in os.walk(directory):
        for dir_name in dirs:
            subfolders.append(os.path.join(root, dir_name))
    return subfolders


def get_lang_by_filename(file_name):
    """通过音频名称获取语音"""
    for lang in language.values():
        if lang in file_name:
            return lang


def get_lang_by_filepath(file_path):
    """通过音频名称获取语音"""
    for lang in language.keys():
        if lang + "\\snd\\effect" in file_path:
            return language[lang]


def thread_it(func, *args):
    """将函数打包进线程"""
    # 创建
    t = threading.Thread(target=func, args=args)
    # 守护
    t.setDaemon(True)
    # 启动
    t.start()


class LanguageChecker:
    def __init__(self, lang_window_name):
        self.lang_window_name = lang_window_name
        self.lang_window_name.title("国际化音频校验  1.00.00")
        self.width = 490
        self.height = 590
        self.lang_window_name.geometry(str(self.width) + 'x' + str(self.height))

        # 共享音频处理
        self.file_path_frame = LabelFrame(self.lang_window_name, text="【共享文件音频处理】")
        self.file_path_frame.grid(row=0, column=0, padx=10, pady=10)
        windnd.hook_dropfiles(self.file_path_frame, func=self.dragg)
        self.file_path_label = Label(self.file_path_frame, text="音频路径（将文件拖入文本框）：")
        self.file_path_label.grid(row=0, column=0, sticky="w")
        self.file_path_text = Text(self.file_path_frame, width=40, height=4)
        self.file_path_text.grid(row=1, column=0, sticky="w")
        self.latest_files_button = Button(self.file_path_frame, text="获取修改的文件",
                                          command=lambda: thread_it(self.start_batch_latest_files))
        self.latest_files_button.grid(row=0, column=1)
        self.lang_massage_label = Text(self.file_path_frame, width=25, height=4)
        self.lang_massage_label.grid(row=1, column=1, padx=3)
        self.lang_massage_label.configure(state="disabled")

        # 游戏音频处理
        self.file_path_frame2 = LabelFrame(self.lang_window_name, text="【游戏语音处理】")
        self.file_path_frame2.grid(row=1, column=0, padx=10)
        windnd.hook_dropfiles(self.file_path_frame2, func=self.dragg_2)  # 设置拖动获取文件的区域

        self.file_path_label2 = Label(self.file_path_frame2, text="游戏语音路径（将文件拖入文本框）：")
        self.file_path_label2.grid(row=0, column=0, sticky="w")
        self.file_path_text2 = Text(self.file_path_frame2, width=40, height=4)
        self.file_path_text2.grid(row=1, column=0)
        self.batch_check_button = Button(self.file_path_frame2, text="批量比对音频",
                                         command=lambda: thread_it(self.start_batch_check))
        self.batch_check_button.grid(row=0, column=1)
        self.lang_massage_label2 = Text(self.file_path_frame2, width=25, height=4)
        self.lang_massage_label2.grid(row=1, column=1, padx=3)
        self.lang_massage_label2.configure(state="disabled")

        # 按钮区域
        self.button_frame = Frame(self.lang_window_name)
        self.button_frame.grid(row=2, column=0)
        # 开始比对按钮
        self.check_button = Button(self.button_frame, text="单语言对比", command=lambda: thread_it(self.start_check))
        self.check_button.grid(row=0, column=0)

        # 日志
        self.log_frame = LabelFrame(self.lang_window_name, text="日志")
        self.log_frame.grid(row=3, column=0)
        self.log_text = Text(self.log_frame, width=65, height=22)
        self.log_text.grid(row=0, column=0)
        self.log_text.tag_configure("标题", foreground="blue")
        self.log_text.tag_configure("成功", foreground="green")
        self.log_text.tag_configure("失败", foreground="red")

        # 共享文件中有修改的文件，根据语言保存成字典
        self.shared_file_by_lang = {}

    def dragg(self, files):
        # 拖动读取文件地址的方法
        msg = '\n'.join((item.decode("gbk") for item in files))
        self.file_path_text.delete("1.0", "end")
        self.file_path_text.insert("1.0", msg)

    def dragg_2(self, files):
        msg = '\n'.join((item.decode("gbk") for item in files))
        self.file_path_text2.delete("1.0", "end")
        self.file_path_text2.insert("1.0", msg)

    def insert_text(self, text_content, tag=None):
        self.log_text.insert("end", text_content + "\n", tag)

    def lang_msg_text(self, text_content):
        self.lang_massage_label.configure(state="normal")
        self.lang_massage_label.delete("1.0", "end")
        self.lang_massage_label.insert("end", text_content)
        self.lang_massage_label.configure(state="disabled")

    def lang_msg_text2(self, text_content):
        self.lang_massage_label2.configure(state="normal")
        self.lang_massage_label2.delete("1.0", "end")
        self.lang_massage_label2.insert("end", text_content)
        self.lang_massage_label2.configure(state="disabled")

    def compare_files_md5(self, file1, file2):
        """比对两个文件的MD5值"""
        md5_file1 = calculate_md5(file1)
        md5_file2 = calculate_md5(file2)

        if md5_file1 and md5_file2:
            # print(f"文件 {file1} 的MD5值: {md5_file1}")
            # print(f"文件 {file2} 的MD5值: {md5_file2}")
            return md5_file1 == md5_file2
        else:
            return False

    def latest_files(self, directory):
        """找出文件夹内最近更新的文件"""
        files_by_date = get_files_by_modification_date(directory)

        if not files_by_date:
            self.insert_text("目录中没有文件")
            return

        files_total_num = 0
        for value in files_by_date.values():
            files_total_num += len(value)

        # 找到修改时间最晚的那个键
        latest_time = max(files_by_date.keys())
        self.insert_text(f"【共享音频文件】文件总数：{files_total_num}，最新修改时间: {latest_time}", "标题")

        if len(files_by_date) == 1:
            self.insert_text(f"所有文件都修改了或都没有改。")
            return

        # 打印最新修改时间的文件列表
        self.insert_text("对应的音频列表如下:", "成功")
        for filename in files_by_date[latest_time]:
            self.insert_text(filename)
        return files_by_date[latest_time]

    def check_files_in_folders(self, folder1, folder2):
        """检查文件夹1内的文件是否在文件夹2中存在，并比较MD5值"""
        latest_files = self.latest_files(folder1)  # 获取文件夹内新更新的音频，用于外包反馈核对
        for root, _, files in os.walk(folder1):
            for file in files:
                file1_path = os.path.join(root, file)
                file2_path = os.path.join(folder2, file)

                if os.path.exists(file2_path):
                    flag = "【修改文件】" if file in latest_files else ""
                    if self.compare_files_md5(file1_path, file2_path):
                        if flag:
                            self.insert_text(flag + f"文件 '{file}' 在两个文件夹中是相同的。", "成功")
                    else:
                        self.insert_text(flag + f"【失败】文件 '{file}' 在两个文件夹中是不同的。", "失败")
                # else:
                #     print(f"文件 '{file}' 在文件夹 {folder2} 中不存在。")

    def start_batch_latest_files(self):
        """批量找出文件夹内最近更新的文件"""
        self.shared_file_by_lang.clear()  # 清空文件地址缓存
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.lang_massage_label.delete("1.0", "end")
        folder1 = str(self.file_path_text.get("1.0", "end")).strip()

        subfolders = get_all_subfolders(folder1)  # 获取所有子文件夹
        modify_lang = []
        for folder in subfolders:
            lang = get_lang_by_filename(os.path.basename(folder))
            self.shared_file_by_lang.update({lang: folder})
            self.insert_text(f"====检测语言【{lang}】=====", "标题")
            result = self.latest_files(folder)
            if result:
                modify_lang.append(lang)
                self.lang_msg_text(f"检测到语言：\n{modify_lang}")
        self.log_text.configure(state="disabled")

    def start_batch_check(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.lang_massage_label2.delete("1.0", "end")
        folder2_list = str(self.file_path_text2.get("1.0", "end")).strip().split('\n')

        if not self.shared_file_by_lang or not folder2_list:
            self.insert_text("检查这些步骤做了吗：\n1、获取共享修改的文件；\n2、将游戏音频的压缩包拖入游戏路径输入框")
            self.log_text.configure(state="disabled")
            return

        checked_lang = []
        for file in folder2_list:
            # 将压缩包转换为文件并获取语言路径
            path_cache = zip_to_file(file)
            file_path = get_lang_path(path_cache)
            lang = get_lang_by_filepath(str(file_path))
            checked_lang.append(lang)

            self.insert_text(f"=========核对语言【{lang}】=========", "标题")

            # 检查共享文件中的对应语言文件
            lang_path = self.shared_file_by_lang.get(lang)
            if lang_path:
                self.check_files_in_folders(lang_path, file_path)
                self.lang_msg_text2(f"已处理语言：\n{checked_lang}")
            else:
                self.insert_text(f"共享文件上没有找到对应语言文件", "失败")

            self.insert_text(f"=============核对完成===============", "标题")

            # 使用上下文管理器确保缓存路径正确删除
            shutil.rmtree(path_cache)
        self.log_text.configure(state="disabled")

    def start_check(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        folder1 = str(self.file_path_text.get("1.0", "end")).strip()
        folder2 = str(self.file_path_text2.get("1.0", "end")).strip()

        if not folder1 or not folder2:
            self.insert_text("请选择文件")
            return

        if not os.path.isdir(folder2):
            path_cache = zip_to_file(folder2)  # 解压
            self.check_files_in_folders(folder1, get_lang_path(path_cache))
            shutil.rmtree(path_cache)
        else:
            self.check_files_in_folders(folder1, folder2)

        self.log_text.configure(state="disabled")


def show_lang_window():
    lang_toplevel = Toplevel()
    LanguageChecker(lang_toplevel)


if __name__ == '__main__':
    lang_window = Tk()
    LanguageChecker(lang_window)
    lang_window.mainloop()
