from tkinter import ttk
import numpy as np
from DataRequester import header_config, DataRequester, CheckPackageData, PageData, get_all_lang_packagedatda
from FrameUI import *


class PackageDataChecker:
    def __init__(self, data_check_window):
        self.data_check_window = data_check_window
        self.data_check_window.title("数据核验工具 1.00.02")
        self.width = 600
        self.height = 300
        self.data_check_window.geometry(str(self.width) + 'x' + str(self.height))

        self.packagedata_frame = LabelFrame(self.data_check_window)

        self.country_label = Label(self.packagedata_frame, text="国家：", width=12)
        self.country = ttk.Combobox(self.packagedata_frame, values=list(header_config["country"].keys()), width=20)
        self.country.current(0)

        self.language_label = Label(self.packagedata_frame, text="语言：", width=12)
        self.language = ttk.Combobox(self.packagedata_frame, values=list(header_config["language"].keys()), width=20)
        self.language.current(0)

        self.platform_label = Label(self.packagedata_frame, text="平台：", width=12)
        self.platform = ttk.Combobox(self.packagedata_frame, values=list(header_config["platform"].keys()), width=20)
        self.platform.current(0)

        self.resourceTypeCode_label = Label(self.packagedata_frame, text="资源：", width=12)
        self.resourceTypeCode = ttk.Combobox(self.packagedata_frame, values=["X2", "X4"], width=20)
        self.resourceTypeCode.current(0)

        self.validate_command = self.packagedata_frame.register(self.validate_input)

        self.version_label = Label(self.packagedata_frame, text="版本号：", width=10)
        self.version_var = StringVar()
        self.version_entry = Entry(self.packagedata_frame, textvariable=self.version_var, validate='key',
                                   validatecommand=(self.validate_command, "%S"), width=20)

        self.environment_label = Label(self.packagedata_frame, text="环境：", width=12)
        self.environment = ttk.Combobox(self.packagedata_frame, values=["正式线", "测试线"], width=20)
        self.environment.current(0)

        self.package_ident = Label(self.packagedata_frame, text="子包标识：", width=10)
        self.ident_var = StringVar()
        self.ident_entry = Entry(self.packagedata_frame, textvariable=self.ident_var, width=20)

        self.packagedata_button = Button(self.packagedata_frame, text="获取", width=8,
                                         command=self.package_data_request)
        self.expanddata_button = Button(self.packagedata_frame, text="获取脑力开发页面数据配置", width=20,
                                        command=self.expand_data_config)

        self.allpackagedata_frame = LabelFrame(self.packagedata_frame, text="【获取13国语言全部资源】")
        self.alllangpackagedata_button = Button(self.allpackagedata_frame, text="子包", width=20,
                                                command=self.all_lang_package_data)
        self.attention_label = Label(self.allpackagedata_frame,
                                     text="注意：【获取13国语言全部资源】无需选择语言和资源，输出给定子包标识x2、x4下13国语言MD5信息")

        self.packagedata_frame.grid(row=0, column=0, sticky="N", padx=10, pady=10)

        self.country_label.grid(row=0, column=0, padx=2, pady=5)
        self.country.grid(row=0, column=1)
        self.language_label.grid(row=0, column=2)
        self.language.grid(row=0, column=3)
        self.platform_label.grid(row=1, column=0, padx=2, pady=5)
        self.platform.grid(row=1, column=1)
        self.resourceTypeCode_label.grid(row=1, column=2)
        self.resourceTypeCode.grid(row=1, column=3)
        self.version_label.grid(row=2, column=0)
        self.version_entry.grid(row=2, column=1)
        self.environment_label.grid(row=2, column=2)
        self.environment.grid(row=2, column=3, padx=5)
        self.package_ident.grid(row=3, column=0)
        self.ident_entry.grid(row=3, column=1, padx=2, pady=5)
        self.packagedata_button.grid(row=4, column=0, columnspan=3)
        self.expanddata_button.grid(row=4, column=3)
        self.allpackagedata_frame.grid(row=5, column=0, columnspan=4, sticky="N", padx=5, pady=10)
        self.alllangpackagedata_button.grid(row=5, column=0)
        self.attention_label.grid(row=6, column=0, columnspan=4)

    # 获取 data_check_window 对象
    def get_data_check_window(self):
        return self.data_check_window

    # 获取给定子包标识的子包信息
    def package_data_request(self):
        platform = self.platform.get()
        version = self.version_entry.get()
        environment = self.environment.get()
        language = self.language.get()
        country = self.country.get()
        resource_type_code = self.resourceTypeCode.get()
        ident_value = self.ident_entry.get()

        # 检查版本号和子包标识是否为空
        if not version or not ident_value:
            messagebox.showinfo("查询失败 ", "请输入版本号和子包标识!", parent=self.data_check_window)
            return
        # 创建数据请求对象
        data_requester = DataRequester(platform, version, language, environment, country)

        # 创建请求体并获取首页数据
        body = data_requester.make_packagedata_body([ident_value], resource_type_code=resource_type_code)
        package_data = data_requester.packagedata(body)

        # 校验子包MD5
        file_info = CheckPackageData(package_data).is_exist_FileInfo()

        file_info_array = np.array(file_info, dtype=object)

        # 在数组中插入资源类型和语言信息
        result_arr = np.insert(file_info_array, (1, 1), (resource_type_code, language), axis=1)

        # 输出结果
        output_result(result_arr, package_headers)

    # 获取脑力开发年龄配置
    def expand_data_config(self):
        platform = self.platform.get()
        version = self.version_entry.get()
        environment = self.environment.get()
        language = self.language.get()
        country = self.country.get()
        # 检查版本号和子包标识是否为空
        if not version:
            messagebox.showinfo("查询失败 ", "请输入版本号", parent=self.data_check_window)
            return
        # 创建数据请求对象
        data_requester = DataRequester(platform, version, language, environment, country)
        result = PageData(data_requester.page_data("脑力开发")).get_age_config_by_expanddata()
        title = platform + "_" + version + "版本_" + environment + "_" + language + "_" + country + "_" + "脑力开发页面年龄配置"
        output_result(result, expand_age_headers, title)

    def all_lang_package_data(self):
        """
        展示13国语言子包信息
        :return:
        """
        platform = self.platform.get()
        version = self.version_entry.get()
        environment = self.environment.get()
        country = self.country.get()
        ident_value = self.ident_entry.get()

        # 检查版本号和子包标识是否为空
        if not version or not ident_value:
            messagebox.showinfo("查询失败 ", "请输入版本号和子包标识!", parent=self.data_check_window)
            return

        # 获取13国语言子包信息
        result_arr = get_all_lang_packagedatda([ident_value], platform, version, environment, country)
        # 输出结果
        output_result(result_arr, package_headers)

    # 允许输入的字符：数字（0-9）
    def validate_input(self, char):
        return char.isdigit()  # 验证输入的字符是否为数字


def show_data_check_window():
    data_check_toplevel = Toplevel()
    PackageDataChecker(data_check_toplevel)


if __name__ == '__main__':
    data_check_window = Tk()  # 实例化出一个父窗口
    PackageDataChecker(data_check_window)
    data_check_window.mainloop()
