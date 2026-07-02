import tkinter as tk
from tkinter import Toplevel
import subprocess
import os
import zipfile
import json
import windnd


class HDCCommandWindow:
    def __init__(self, parent):
        self.root = Toplevel(parent)
        self.root.title("鸿蒙测试工具  1.00.03")
        self.root.geometry("650x450")
        if parent:
            self.root.transient(parent)  # 跟随父窗口

        self.create_ui()

    def create_ui(self):
        # 文件路径
        file_path_label = tk.Label(self.root, text="文件路径:")
        file_path_label.grid(row=0, column=0, padx=10, pady=5)

        self.file_path_text = tk.Text(self.root, height=2, width=50)
        self.file_path_text.grid(row=0, column=1, padx=10, pady=5)

        # 应用包名
        package_name_label = tk.Label(self.root, text="应用包名:")
        package_name_label.grid(row=1, column=0, padx=10, pady=5)

        self.package_name_text = tk.Text(self.root, height=2, width=50)
        self.package_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.package_name_text.insert("1.0", "com.sinyee.babybus.mathIII.hos")

        # 获取并设置包名按钮
        extract_button = tk.Button(self.root, text="设置包名", command=self.extract_bundle_name)
        extract_button.grid(row=1, column=2, padx=10, pady=5)

        # 拖放支持
        windnd.hook_dropfiles(self.root, func=self.dragg)

        # 功能按钮
        buttons_info = [
            ("获取连接设备", lambda: self.execute_hdc_command(["hdc", "shell", "param", "get", "const.product.name"])),
            ("安装应用", lambda: self.execute_hdc_command(["hdc", "install", self.file_path_text.get("1.0", "end").strip()])),
            ("覆盖安装", lambda: self.execute_hdc_command(["hdc", "install", "-r", self.file_path_text.get("1.0", "end").strip()])),
            ("卸载应用", lambda: self.execute_hdc_command(["hdc", "uninstall", self.package_name_text.get("1.0", "end").strip()])),
            ("清除应用数据", lambda: (
                self.execute_hdc_command(["hdc", "shell", "bm", "clean", "-d", "-n", self.package_name_text.get('1.0', 'end').strip()]),
                self.execute_hdc_command(["hdc", "shell", "bm", "clean", "-c", "-n", self.package_name_text.get('1.0', 'end').strip()])
            )),
            ("启动应用", lambda: self.execute_hdc_command(
                ["hdc", "shell", "aa", "start", "-a", "EntryAbility", "-b", self.package_name_text.get('1.0', 'end').strip()])),
        ]

        for index, (text, command) in enumerate(buttons_info):
            button = tk.Button(self.root, text=text, command=command)
            row = (index // 3) + 2
            column = index % 3
            button.grid(row=row, column=column, padx=10, pady=10)

        # 输出框
        self.output_text = tk.Text(self.root, height=10, width=50)
        self.output_text.grid(row=len(buttons_info) // 2 + 3, column=0, columnspan=2, pady=10)

    def execute_hdc_command(self, cmd_list):
        try:
            output = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, output.decode('utf-8', errors='ignore'))
        except subprocess.CalledProcessError as e:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "Error:\n" + e.output.decode('utf-8', errors='ignore'))
        except Exception as e:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"Exception: {str(e)}")

    def extract_bundle_name(self):
        file_path = self.file_path_text.get("1.0", "end").strip().split('\n')[0].strip()

        if not file_path:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "错误：文件路径为空，请先选择或拖入 hap 文件")
            return

        if not os.path.exists(file_path):
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"错误：文件不存在\n{file_path}")
            return

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                bundle_name = None
                for json_name in ['module.json', 'config.json']:
                    if json_name in zf.namelist():
                        with zf.open(json_name) as f:
                            data = json.load(f)
                            if 'app' in data and isinstance(data['app'], dict) and 'bundleName' in data['app']:
                                bundle_name = data['app']['bundleName']
                                break

                if bundle_name:
                    self.package_name_text.delete("1.0", "end")
                    self.package_name_text.insert("1.0", bundle_name)
                    self.output_text.delete(1.0, tk.END)
                    self.output_text.insert(tk.END, f"成功提取包名：{bundle_name}")
                else:
                    self.output_text.delete(1.0, tk.END)
                    self.output_text.insert(tk.END, "错误：未能从 hap 文件中解析到包名（未找到 app.bundleName）")
        except zipfile.BadZipFile:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "错误：文件不是有效的 hap/zip 格式")
        except Exception as e:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"提取包名失败：{str(e)}")

    def dragg(self, files):
        if isinstance(files, (str, bytes)):
            files = [files]

        paths = []
        for item in files:
            if isinstance(item, bytes):
                paths.append(item.decode("gbk"))
            else:
                paths.append(item)

        msg = '\n'.join(paths)
        self.file_path_text.delete("1.0", "end")
        self.file_path_text.insert("1.0", msg)


def show_hdc_window(parent=None):
    """供 FastInstall.py 调用的入口函数"""
    HDCCommandWindow(parent)