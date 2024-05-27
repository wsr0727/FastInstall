from tkinter import *
from tkinter import ttk, font, messagebox
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
    # 创建标题
    for col_index, col_name in enumerate(columns):
        header_label = tk.Label(table_frame, text=col_name, **header_style)
        header_label.grid(row=0, column=col_index, sticky="nsew")

    # 创建内容
    for row_index, row_data in enumerate(data, start=1):
        for col_index, cell_data in enumerate(row_data):
            content_btn = Button(table_frame, text=cell_data, foreground="red" if "不存在" in cell_data else "black",
                                 **content_style)
            content_btn.grid(row=row_index, column=col_index, sticky="nsew")
            # 绑定双击事件
            content_btn.bind("<Double-1>", copy_to_clipboard)

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


def output_result(result_arr):
    if result_arr.size != 0:
        # 创建一个新的Toplevel窗口
        log_top = Toplevel()
        log_top.title("子包信息查询结果")
        table_frame = ttk.Frame(log_top)
        table_frame.grid(row=0, column=0, sticky='N')
        create_table(table_frame, ("PackageIdent", "title", "LangFileInfo_MD5", "PackageFileInfo_MD5"), result_arr)
    else:
        messagebox.showinfo("查询失败 ", "查询结果为空！")
