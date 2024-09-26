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
import pandas as pd

# 打包指令（仅打包国际化音频校验工具） pyinstaller -F -w LanguageChecker.py
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


def compare_files_md5(file1, file2):
    """比对两个文件的MD5值"""
    md5_file1 = calculate_md5(file1)
    md5_file2 = calculate_md5(file2)

    if md5_file1 and md5_file2:
        return md5_file1 == md5_file2
    else:
        return False


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
    """通过音频名称获取语言"""
    for lang in language.values():
        if lang in file_name:
            return lang


def get_lang_by_filepath(file_path):
    """获取文件路径中的语言信息"""
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


class ExcelProcess:
    @staticmethod
    def return_engine_by_endswith(file_path):
        if file_path.endswith('.xlsx'):
            return 'openpyxl'
        elif file_path.endswith('.xls'):
            return 'xlrd'
        else:
            raise ValueError("文件类型不支持，只支持 .xlsx 和 .xls 格式")

    def read_excel_1st_col_as_dict(self, excel_file_path):
        """读取xlsx 或 csv 文件的第一列数据并返回字典。{语音：[第一列音频名称]}"""
        # 读取Excel文件
        xls = pd.ExcelFile(excel_file_path, engine=self.return_engine_by_endswith(excel_file_path))

        # 获取所有工作表的名称
        sheet_names = xls.sheet_names
        feedback_audios = {}

        for sheet_name in sheet_names:
            # 工作表的数据
            name = next((lang for lang in language.values() if lang in sheet_name), sheet_name)
            df = pd.read_excel(xls, sheet_name=sheet_name, engine=self.return_engine_by_endswith(excel_file_path))
            # 获取第一列的数据并转换为列表
            audio_list = df.iloc[0:, 0].tolist()  # 将第一列数据转换为列表
            # 过滤掉nan值
            feedback_audios.update({name: [value for value in audio_list if not pd.isna(value)]})

        return feedback_audios

    def read_excel_1st_col_as_list(self, file_path):
        """读取xlsx 或 csv 文件的第一列数据并返回列表"""
        df = pd.read_excel(file_path, engine=self.return_engine_by_endswith(file_path))

        # 获取第一列的数据并转换为列表
        first_column_list = df.iloc[2:, 0].tolist()  # 将第一列数据转换为列表
        # 过滤掉nan值
        first_column_list = [value for value in first_column_list if not pd.isna(value)]

        return first_column_list


class LanguageChecker:
    def __init__(self, lang_window_name):
        self.lang_window_name = lang_window_name
        self.lang_window_name.title("国际化音频校验  1.00.01")
        self.width = 860
        self.height = 590
        self.lang_window_name.geometry(str(self.width) + 'x' + str(self.height))

        # 共享音频处理
        self.file_path_frame = LabelFrame(self.lang_window_name, text="【共享文件音频处理】")
        self.file_path_frame.grid(row=0, column=0, padx=10, pady=10)

        self.file_path_label = Label(self.file_path_frame, text="音频路径（将文件拖入文本框）：")
        self.file_path_label.grid(row=0, column=0, sticky="w")
        self.file_path_text = Text(self.file_path_frame, width=40, height=4)
        self.file_path_text.grid(row=1, column=0, sticky="w")
        windnd.hook_dropfiles(self.file_path_text, func=lambda files: self.dragg(files, self.file_path_text))

        self.latest_files_button = Button(self.file_path_frame, text="获取修改的文件",
                                          command=lambda: thread_it(self.start_batch_latest_files))
        self.latest_files_button.grid(row=0, column=1)
        self.lang_massage_label = Text(self.file_path_frame, width=25, height=4)
        self.lang_massage_label.grid(row=1, column=1, padx=3)
        self.lang_massage_label.configure(state="disabled")

        # 游戏音频处理
        self.game_file_path_frame = LabelFrame(self.lang_window_name, text="【游戏语音处理】")
        self.game_file_path_frame.grid(row=1, column=0, padx=10)

        self.file_path_label2 = Label(self.game_file_path_frame, text="游戏语音路径（将文件拖入文本框）：")
        self.file_path_label2.grid(row=0, column=0, sticky="w")
        self.file_path_text2 = Text(self.game_file_path_frame, width=40, height=4)
        self.file_path_text2.grid(row=1, column=0)
        windnd.hook_dropfiles(self.file_path_text2, func=lambda files: self.dragg(files, self.file_path_text2))
        self.batch_check_button = Button(self.game_file_path_frame, text="批量比对音频",
                                         command=lambda: thread_it(self.start_batch_check))
        self.batch_check_button.grid(row=0, column=1)
        self.lang_massage_label2 = Text(self.game_file_path_frame, width=25, height=4)
        self.lang_massage_label2.grid(row=1, column=1, padx=3)
        self.lang_massage_label2.configure(state="disabled")

        # 表格数据处理
        self.excel_file_path_frame = LabelFrame(self.lang_window_name, text="【共享音频与反馈表格对比】")
        self.excel_file_path_frame.grid(row=0, column=1)

        self.excel_file_path_label = Label(self.excel_file_path_frame,
                                           text="外包反馈表格（将文件拖入文本框，仅支持xls、xlsx）：")
        self.excel_file_path_label.grid(row=0, column=0, sticky="w")
        self.excel_file_path_text = Text(self.excel_file_path_frame, width=50, height=4)
        self.excel_file_path_text.grid(row=1, column=0, columnspan=2)
        # 设置拖动获取文件的区域
        windnd.hook_dropfiles(self.excel_file_path_text,
                              func=lambda files: self.dragg(files, self.excel_file_path_text))
        self.excel_lang_check_button = Button(self.excel_file_path_frame, text="比对",
                                              command=lambda: thread_it(self.start_latest_files_feedback_excel_check))
        self.excel_lang_check_button.grid(row=0, column=1)

        self.excel_file_path_frame2 = LabelFrame(self.lang_window_name, text="【游戏音频与差异表格对比】")
        self.excel_file_path_frame2.grid(row=1, column=1)

        self.excel_file_path_label2 = Label(self.excel_file_path_frame2,
                                            text="全语言差异表（将文件拖入文本框，仅支持xls、xlsx）：")
        self.excel_file_path_label2.grid(row=0, column=0, sticky="w")
        self.excel_file_path_text2 = Text(self.excel_file_path_frame2, width=50, height=4)
        self.excel_file_path_text2.grid(row=1, column=0, columnspan=2)
        windnd.hook_dropfiles(self.excel_file_path_text2,
                              func=lambda files: self.dragg(files, self.excel_file_path_text2))

        self.batch_check_button = Button(self.excel_file_path_frame2, text="比对",
                                         command=lambda: thread_it(self.start_lang_file_integrity_check))
        self.batch_check_button.grid(row=0, column=1)

        # 按钮区域
        self.button_frame = Frame(self.lang_window_name)
        self.button_frame.grid(row=2, column=0)
        # 开始比对按钮
        self.check_button = Button(self.button_frame, text="单语言对比", command=lambda: thread_it(self.start_check))
        self.check_button.grid(row=0, column=0)

        # 音频比对日志
        self.log_frame = LabelFrame(self.lang_window_name, text="音频比对日志")
        self.log_frame.grid(row=3, column=0)
        self.log_text = Text(self.log_frame, width=66, height=22)
        self.log_text.grid(row=0, column=0)
        self.style_configure(self.log_text)

        # 表格比对日志
        self.excel_log_frame = LabelFrame(self.lang_window_name, text="表格比对日志")
        self.excel_log_frame.grid(row=3, column=1)
        self.excel_log_text = Text(self.excel_log_frame, width=50, height=22)
        self.excel_log_text.grid(row=0, column=0)
        self.style_configure(self.excel_log_text)

        # 共享文件中每个语言对应的文件夹，根据语言保存成字典
        self.shared_file_by_lang = {}
        # 共享文件中有修改的音频名称，根据语言保存成字典
        self.shared_audio_by_lang = {}

    @staticmethod
    def style_configure(log_widget):
        """在文本框末尾插入text_content"""
        log_widget.tag_configure("标题", foreground="blue")
        log_widget.tag_configure("成功", foreground="green")
        log_widget.tag_configure("失败", foreground="red")

    @staticmethod
    def insert_text(log_widget, text_content, tag=None):
        """在文本框末尾插入text_content"""
        log_widget.configure(state="normal")
        log_widget.insert("end", text_content + "\n", tag)
        log_widget.configure(state="disabled")

    @staticmethod
    def dragg(files, target_text_widget):
        """拖动读取文件地址的方法"""
        msg = '\n'.join((item.decode("gbk") for item in files))
        target_text_widget.delete("1.0", "end")
        target_text_widget.insert("1.0", msg)

    @staticmethod
    def lang_msg_text(text_content, label):
        """清空文本框并插入text_content"""
        label.configure(state="normal")
        label.delete("1.0", "end")
        label.insert("end", text_content)
        label.configure(state="disabled")

    @staticmethod
    def get_text(target_text_widget):
        """获取文本框文案"""
        return str(target_text_widget.get("1.0", "end")).strip()

    @staticmethod
    def delete_text(target_text_widget):
        """删除文本框内容"""
        target_text_widget.configure(state="normal")
        target_text_widget.delete("1.0", "end")
        target_text_widget.configure(state="disabled")

    def latest_files(self, directory):
        """找出文件夹内最近更新的文件"""
        files_by_date = get_files_by_modification_date(directory)

        if not files_by_date:
            self.insert_text(self.log_text, "目录中没有文件")
            return

        files_total_num = 0
        for value in files_by_date.values():
            files_total_num += len(value)

        # 找到修改时间最晚的那个键
        latest_time = max(files_by_date.keys())
        self.insert_text(self.log_text, f"【共享音频文件】文件总数：{files_total_num}，最新修改时间: {latest_time}", "标题")

        if len(files_by_date) == 1:
            self.insert_text(self.log_text, f"所有文件都修改了或都没有改。")
            return

        # 打印最新修改时间的文件列表
        self.insert_text(self.log_text, "  对应的音频列表如下:", "成功")
        for filename in files_by_date[latest_time]:
            self.insert_text(self.log_text, "    " + filename)
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
                    if compare_files_md5(file1_path, file2_path):
                        if flag:
                            self.insert_text(self.log_text, flag + f"文件 '{file}' 在两个文件夹中是相同的。", "成功")
                    else:
                        self.insert_text(self.log_text, flag + f"【失败】文件 '{file}' 在两个文件夹中是不同的。", "失败")

    def start_batch_latest_files(self):
        """【获取修改文件】批量找出文件夹内最近更新的文件"""
        self.shared_file_by_lang.clear()  # 清空文件地址缓存
        self.shared_audio_by_lang.clear()
        self.delete_text(self.log_text)
        self.delete_text(self.lang_massage_label)
        folder1 = self.get_text(self.file_path_text)
        if not folder1:
            self.insert_text(self.log_text, "请输入需要检查的音频路径。", "失败")
            return False

        subfolders = get_all_subfolders(folder1)  # 获取所有子文件夹
        for folder in subfolders:
            lang = get_lang_by_filename(os.path.basename(folder))
            self.shared_file_by_lang.update({lang: folder})
            self.insert_text(self.log_text, f"====检测语言【{lang}】=====", "标题")
            result = self.latest_files(folder)
            if result:
                self.shared_audio_by_lang.update({lang: result})
                self.lang_msg_text(f"检测到语言：\n{', '.join(map(str, self.shared_audio_by_lang))}",
                                   self.lang_massage_label)
        return True

    def start_batch_check(self):
        """【批量比对音频】在获取修改文件的基础上，解压游戏语音包，与共享文件上的音频比对MD5"""
        self.delete_text(self.log_text)
        self.delete_text(self.lang_massage_label2)
        folder2_list = self.get_text(self.file_path_text2).split('\n')

        if not self.shared_file_by_lang or not folder2_list:
            self.insert_text(self.log_text,
                             "检查这些步骤做了吗：\n1、获取共享修改的文件；\n2、将游戏音频的压缩包拖入游戏路径输入框")
            self.log_text.configure(state="disabled")
            return

        checked_lang = []
        for file in folder2_list:
            # 将压缩包转换为文件并获取语言路径
            path_cache = zip_to_file(file)
            file_path = get_lang_path(path_cache)
            lang = get_lang_by_filepath(str(file_path))
            checked_lang.append(lang)

            self.insert_text(self.log_text, f"=========核对语言【{lang}】=========", "标题")

            # 检查共享文件中的对应语言文件
            lang_path = self.shared_file_by_lang.get(lang)
            if lang_path:
                self.check_files_in_folders(lang_path, file_path)
                self.lang_msg_text(f"已处理语言：\n{', '.join(checked_lang)}", self.lang_massage_label2)
            else:
                self.insert_text(self.log_text, f"共享文件上没有找到对应语言文件", "失败")

            self.insert_text(self.log_text, f"=============核对完成===============", "标题")

            # 使用上下文管理器确保缓存路径正确删除
            shutil.rmtree(path_cache)

    def start_latest_files_feedback_excel_check(self):
        """【共享音频与反馈表格对比】先获取共享音频中有修改的音频文件，再与反馈表对比"""
        self.delete_text(self.excel_log_text)
        if not self.shared_audio_by_lang:
            if not self.start_batch_latest_files():
                return

        feedback_excel = self.get_text(self.excel_file_path_text)  # 差异表，即正确音频目录
        if not feedback_excel:
            self.insert_text(self.excel_log_text, "请输入外包反馈表格地址", "失败")
            return
        audio_dict = ExcelProcess().read_excel_1st_col_as_dict(feedback_excel)
        # 去除“.mp3”后缀
        shared_audio_by_lang = {lang: [filename.replace('.mp3', '') for filename in filenames] for lang, filenames in
                                self.shared_audio_by_lang.items()}

        self.insert_text(self.excel_log_text, "====【共享音频与反馈表格对比】开始====", "标题")
        for key in audio_dict.keys():
            self.insert_text(self.excel_log_text, f"----【{key}】----", "标题")
            if key not in shared_audio_by_lang.keys():
                self.insert_text(self.excel_log_text, f"    共享文件中缺少补配文件。", "失败")
                continue
            if set(audio_dict[key]) != set(shared_audio_by_lang[key]):
                for audio in audio_dict[key]:
                    if audio not in set(shared_audio_by_lang[key]):
                        self.insert_text(self.excel_log_text, f"    共享文件中音频：{audio} 未更新", "失败")
            else:
                self.insert_text(self.excel_log_text, f"    无异常，音频列表：\n    {audio_dict[key]}", "成功")

        self.insert_text(self.excel_log_text, "====【共享音频与反馈表格对比】完成====", "标题")

    def start_lang_file_integrity_check(self):
        """【游戏音频与差异表格对比】二轮全语言完整性检查，批量比对游戏音频与差异表音频列表是否一致"""
        self.delete_text(self.excel_log_text)

        excel_path = self.get_text(self.excel_file_path_text2)  # 差异表，即正确音频目录
        result_list = ExcelProcess().read_excel_1st_col_as_list(excel_path)

        game_lang_path = self.get_text(self.file_path_text2)  # 音频路径
        self.insert_text(self.excel_log_text, "解压中....", "标题")
        package_cache = zip_to_file(game_lang_path)

        if game_lang_path.endswith(".apk"):
            game_lang_path = package_cache + "/assets/res/subModules"
        elif game_lang_path.endswith(".ipa"):
            game_lang_path = package_cache + "/Payload/2d_noSuper_education.app/res/subModules"

        self.insert_text(self.excel_log_text, "开始检测【游戏音频与差异表音频列表是否一致】", "标题")
        for lang in language.keys():
            self.insert_text(self.excel_log_text, f"=====检测语言【{language[lang]}】=======", "标题")
            # 拼接子包内的音频路径
            lang_file_list = []  # 所有内置子包的语音列表
            for package in os.listdir(game_lang_path):
                lang_path = os.path.join(game_lang_path, package, "res", "i18n", lang, "snd", "effect")
                if os.path.exists(lang_path):
                    lang_file_list = lang_file_list + os.listdir(lang_path)

            for file_name in result_list:
                # 获取该文件名在指定文件夹下是否存在
                file_exists = any(os.path.splitext(f)[0] == file_name for f in lang_file_list)
                if not file_exists:
                    # 如果不存在才输出
                    self.insert_text(self.excel_log_text, f"    游戏音频缺少文件文件 '{file_name}'。", "失败")
        self.insert_text(self.excel_log_text, "检测完成【游戏音频与差异表音频列表是否一致】", "标题")
        shutil.rmtree(package_cache)

    def start_check(self):
        """【单语言对比】"""
        self.delete_text(self.log_text)
        folder1 = self.get_text(self.file_path_text)
        folder2 = self.get_text(self.file_path_text2)

        if not folder1 or not folder2:
            self.insert_text(self.log_text, "请选择文件")
            return

        if not os.path.isdir(folder2):
            path_cache = zip_to_file(folder2)  # 解压
            self.check_files_in_folders(folder1, get_lang_path(path_cache))
            shutil.rmtree(path_cache)
        else:
            self.check_files_in_folders(folder1, folder2)


def show_lang_window():
    lang_toplevel = Toplevel()
    LanguageChecker(lang_toplevel)


if __name__ == '__main__':
    lang_window = Tk()
    LanguageChecker(lang_window)
    lang_window.mainloop()
