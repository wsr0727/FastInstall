from tkinter import ttk
from DataRequester import *
from FrameUI import *


# 打包指令 pyinstaller --add-data "chromedriver.exe;." -F -w DataValidator.py

class PackageDataChecker:
    def __init__(self, data_check_window):
        self.data_check_window = data_check_window
        self.data_check_window.title("数据核验工具 1.00.00")
        self.width = 600
        self.height = 500
        self.data_check_window.geometry(str(self.width) + 'x' + str(self.height))

        self.packagedata_frame = LabelFrame(self.data_check_window)

        self.country_label = Label(self.packagedata_frame, text="国家：", width=12)
        self.country = ttk.Combobox(self.packagedata_frame, value=list(header_config["country"].keys()), width=20)
        self.country.current(0)

        self.language_label = Label(self.packagedata_frame, text="语言：", width=12)
        self.language = ttk.Combobox(self.packagedata_frame, value=list(header_config["language"].keys()), width=20)
        self.language.current(0)

        self.platform_label = Label(self.packagedata_frame, text="平台：", width=12)
        self.platform = ttk.Combobox(self.packagedata_frame, value=list(header_config["platform"].keys()), width=20)
        self.platform.current(0)

        self.resourceTypeCode_label = Label(self.packagedata_frame, text="资源：", width=12)
        self.resourceTypeCode = ttk.Combobox(self.packagedata_frame, value=["X2", "X4"], width=20)
        self.resourceTypeCode.current(0)

        self.validate_command = self.packagedata_frame.register(self.validate_input)

        self.version_label = Label(self.packagedata_frame, text="版本号：", width=10)
        self.version_var = StringVar()
        self.version_entry = Entry(self.packagedata_frame, textvariable=self.version_var, validate='key',
                                   validatecommand=(self.validate_command, "%S"), width=20)

        self.environment_label = Label(self.packagedata_frame, text="环境：", width=12)
        self.environment = ttk.Combobox(self.packagedata_frame, value=["正式线", "测试线"], width=20)
        self.environment.current(0)

        self.package_ident = Label(self.packagedata_frame, text="子包标识：", width=10)
        self.ident_var = StringVar()
        self.ident_entry = Entry(self.packagedata_frame, textvariable=self.ident_var, width=20)

        self.subPackageID_label = Label(self.packagedata_frame, text="分包ID：", width=10)
        self.subPackageID_var = StringVar()
        self.subPackageID_entry = Entry(self.packagedata_frame, textvariable=self.subPackageID_var, validate='key',
                                        validatecommand=(self.validate_command, "%S"), width=20)

        self.packagedata_button = Button(self.packagedata_frame, text="获取", width=8,
                                         command=self.package_data_request)

        self.allpackagedata_frame = LabelFrame(self.packagedata_frame, text="【获取13国语言全部资源】")
        self.alllangpackagedata_button = Button(self.allpackagedata_frame, text="子包", width=20,
                                                command=self.all_lang_package_data)
        self.subpackagedata_button = Button(self.allpackagedata_frame, text="分包", width=20,
                                            command=self.subpackagedata)
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
        self.subPackageID_label.grid(row=3, column=2)
        self.subPackageID_entry.grid(row=3, column=3, padx=2, pady=5)
        self.packagedata_button.grid(row=4, column=0, columnspan=4)
        self.allpackagedata_frame.grid(row=5, column=0, columnspan=4, sticky="N", padx=5, pady=10)
        self.alllangpackagedata_button.grid(row=5, column=0)
        self.subpackagedata_button.grid(row=5, column=1)
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
        # 创建数据请求者对象
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

    def subpackagedata(self):
        """
        展示分包信息
        :return:
        """
        # 获取用户输入的信息
        platform = self.platform.get()
        version = self.version_entry.get()
        environment = self.environment.get()
        language = self.language.get()
        country = self.country.get()
        resource_type_code = self.resourceTypeCode.get()
        ident_value = self.ident_entry.get()
        subPackageID = self.subPackageID_entry.get()

        # 检查输入的子包标识是否为空
        if not ident_value:
            messagebox.showinfo("查询失败 ", "请输入子包标识!", parent=self.data_check_window)
            return

        # 创建数据请求对象
        data_requester = DataRequester(platform, version, language, environment, country)

        # 创建请求体并获取首页数据
        body = data_requester.make_packagedata_body([ident_value], resource_type_code=resource_type_code)
        package_data_response = data_requester.packagedata(body)

        # 分包页面数据
        package_data = PackageData(package_data_response)
        subpackage_data = SubPackageData(
            data_requester.get_subpackage_page_data(package_data.get_packageID_by_packagedata())
        )

        # 从分包页面数据中提取分包信息
        subpackage_dict = subpackage_data.extr_subpackage_info()

        # 检查包数据中是否存在文件信息
        packagedata_arr = CheckPackageData(package_data_response).is_exist_FileInfo()

        # 如有指定子包ID，则过滤子包信息
        if subPackageID:
            subpackage_dict = [item for item in subpackage_dict if item['SubPackageID'] == int(subPackageID)]

        # 提取数据并准备输出结果
        result = np.empty((0, 8))
        for subpackage in subpackage_dict:
            sub_id = subpackage['SubPackageID']  # 子包ID
            sub_scene = subpackage['SubPackageScence']  # 子包场景
            sub_config = subpackage['ConfigData']  # 子包配置数据

            # 遍历语言数据
            for lang in subpackage['LangsData']:
                lang_name = lang['lang_name']  # 语言名称
                lang_value = lang['lang_value']  # 语言值

                # 将提取的数据整合为一行
                row = [
                    packagedata_arr[0, 0],
                    sub_id,
                    sub_scene,
                    sub_config,
                    lang_name,
                    lang_value,
                    packagedata_arr[0, 2],
                    packagedata_arr[0, 3]
                ]
                result = np.append(result, [row], axis=0)

        # 输出结果
        output_result(result, subpackage_headers)

    # 允许输入的字符：数字（0-9）
    def validate_input(self, char):
        return char.isdigit()  # 验证输入的字符是否为数字


if __name__ == '__main__':
    data_check_window = Tk()  # 实例化出一个父窗口
    PackageDataChecker(data_check_window)
    data_check_window.mainloop()
