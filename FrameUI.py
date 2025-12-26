from tkinter import *
from tkinter import Scrollbar, messagebox
import tkinter as tk

"""
弹框相关UI
"""
# 定义样式
header_style = {
    "font": ("Arial", 12, "bold"),
    "bg": "lightblue",
    "borderwidth": 2,
    "relief": "groove",
    "padx": 10,
    "pady": 5
}

content_style = {
    "font": ("Arial", 10),
    "bg": "white",
    "borderwidth": 1,
    "relief": "ridge",
    "padx": 10,
    "pady": 5
}

# 定义表头
package_headers = (
    "PackageIdent", "res_type", "lang", "title",
    "PackageFileInfo_MD5", "LangFileInfo_MD5"
)

subpackage_headers = (
    "PackageIdent", "SubPackageID", "SubPackageScence",
    "ConfigData", "lang", "title",
    "PackageFileInfo_MD5", "LangFileInfo_MD5"
)

expand_age_headers = ("区域名称", "区域排序", "子包名称", "子包标识", "总关卡数", "年龄（旧）", "年龄（新）", "核心年龄")


def show_log(task):
    """
    核验数据日志弹框
    :param task: 任务详情
    :return:
    """

    def insert_text(text_content, tag=None):
        log_text.insert("end", text_content + "\n", tag)

    def state_str(state):
        return "成功" if state == 0 else "失败"

    def level_conunt_text(count):
        for i in count:
            insert_text("阶段-" + i["level"] + "：课程数量 " + str(i["count"]))
            insert_text("体验课：" + str(i["free_course"]))
            if i["error"]:
                insert_text("海外存在MV环节的课程：" + str(i["error"]))
            insert_text("-" * 20, "标题")

    def expand_conunt_text(count):
        insert_text("环节总数:" + str(count[0]["count"]))
        insert_text("热门tab总数:" + str(count[0]["热门tab总数"]))
        insert_text("-" * 20, "标题")
        for i in count[0]["data"]:
            for key in i.keys():
                insert_text(key + "：" + str(i[key]))
            insert_text("-" * 20, "标题")

    # 创建一个新的Toplevel窗口
    log_top = Toplevel()
    log_top.title("核验默认数据结果")

    # 在窗口中创建一个文本框来显示日志内容
    log_text = Text(log_top, font="微软雅黑 10 bold")
    log_text.pack()
    # 设置文本和样式
    log_text.tag_configure("标题", foreground="blue")
    log_text.tag_configure("成功", foreground="green")
    log_text.tag_configure("失败", foreground="red")

    log = task["日志"]
    for title, content in log.items():
        insert_text("========" + title + "========", "标题")
        if isinstance(content, dict):
            for t, c in content.items():
                # TODO 代码要整理一下 data_title = {"data": "", "state": "结果", "message": "信息", "file_count": "文件数量（首页+趣味）",
                #               "random_file": "选取的国际化语言文件"}
                if t == "data" and c:
                    try:
                        if c[0]["level"] == "趣味拓展":
                            expand_conunt_text(c)
                        else:
                            level_conunt_text(c)
                    except KeyError:
                        insert_text(f"数据：{c}")
                elif t == "state":
                    insert_text("结果" + "：" + state_str(c), state_str(c))
                elif t == "message":
                    insert_text("信息：" + c)
                elif t == "file_count":
                    insert_text("文件数量（首页+趣味）" + "：" + str(c))
                elif t == "random_file" and c:
                    insert_text("选取的国际化语言文件" + "：" + str(c))
        else:
            insert_text(f"数据：{content}")

    log_text.configure(state="disabled")


def create_table(table_frame, columns, data):
    """
    创建表格到frame
    :param table_frame:表格创建此框架中
    :param columns:表格列名list
    :param data:表格内容二维数组
    """
    # 创建标题
    for col_index, col_name in enumerate(columns):
        header_label = tk.Label(table_frame, text=col_name, **header_style)
        header_label.grid(row=0, column=col_index, sticky="nsew")

    # 处理所有列的合并单元格逻辑
    n_rows = len(data)
    n_cols = len(columns)

    # processed用于标记哪些单元格已经被处理过
    processed = [[False] * n_cols for _ in range(n_rows)]

    # 处理每一列
    for col_index in range(n_cols):
        row_index = 1
        while row_index <= n_rows:
            if row_index > n_rows:
                break
            if processed[row_index - 1][col_index]:
                row_index += 1
                continue

            # 计算合并单元格范围（当前单元格和起始单元格内容相同则row_index自增）
            start = row_index
            while row_index <= n_rows and data[row_index - 1][col_index] == data[start - 1][col_index]:
                row_index += 1
            span = row_index - start

            # 合并单元格并填充内容
            if span > 0:
                content_btn = Button(table_frame, text=data[start - 1][col_index],
                                     foreground="red" if "不存在" in data[start - 1][col_index] else "black",
                                     **content_style)
                content_btn.grid(row=start, column=col_index, rowspan=span, sticky="nsew")

                # 绑定双击事件
                content_btn.bind("<Double-1>", copy_to_clipboard)

                # 标记已处理的单元格
                for row in range(start - 1, row_index - 1):
                    processed[row][col_index] = True

    # 使所有列具有相同的宽度
    for col_index in range(len(columns)):
        table_frame.grid_columnconfigure(col_index, weight=1)

    # 使所有行具有相同的高度
    for row_index in range(len(data) + 1):
        table_frame.grid_rowconfigure(row_index, weight=1)


# 复制文案至剪切板
def copy_to_clipboard(event):
    widget = event.widget
    text = widget.cget("text")
    widget.clipboard_clear()
    widget.clipboard_append(text)
    widget.update()


def output_result(result_arr, headers, title="查询结果"):
    if result_arr.size != 0:
        # 创建一个新的Toplevel窗口
        log_top = Toplevel()
        log_top.title(title)
        log_top.minsize(1100, 750)
        # 创建主框架
        main_frame = Frame(log_top)
        main_frame.pack(fill=BOTH, expand=TRUE)
        # 创建画布
        canvas = Canvas(main_frame, bg='white')
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        # 添加滚动条
        scrollbar = Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.configure(yscrollcommand=scrollbar.set)
        # 创建一个frame在其中放置展示内容
        table_frame = Frame(canvas)
        # 将table_frame放置在canvas上
        canvas.create_window((0, 0), window=table_frame, anchor='nw')

        # 填充内容
        create_table(table_frame, headers, result_arr)
        # 更新canvas的滚动区域
        table_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # 绑定鼠标滚轮事件
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mouse_wheel(event):
            canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        def unbind_mouse_wheel(event):
            canvas.unbind_all("<MouseWheel>")

        # 鼠标事件绑定：进入窗口区域和离开窗口区域
        canvas.bind("<Enter>", bind_mouse_wheel)
        canvas.bind("<Leave>", unbind_mouse_wheel)
    else:
        messagebox.showinfo("查询失败 ", "查询结果为空！")
