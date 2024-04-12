from tkinter import *

"""
弹框相关UI
"""


def show_log(task):
    """
    核验数据日志弹框
    :param task: 任务详情
    :return:
    """

    def state_str(state):
        if state == 0:
            return "成功"
        else:
            return "失败"

    def level_conunt_text(count):
        for i in count:
            log_text.insert("end", "阶段-" + i["level"] + "：课程数量 " + str(i["count"]) + "\n")
            if i["error"]:
                log_text.insert("end", "海外存在MV环节的课程：" + str(i["error"]) + "\n")
            log_text.insert("end", "-" * 20 + "\n", "标题")

    def expand_conunt_text(count):
        log_text.insert("end", "环节总数:" + str(count[0]["count"]) + "\n")
        log_text.insert("end", "热门tab总数:" + str(count[0]["热门tab总数"]) + "\n")
        log_text.insert("end", "-" * 20 + "\n", "标题")
        for i in count[0]["data"]:
            for key in i.keys():
                log_text.insert("end", key + "：" + str(i[key]) + "\n")
            log_text.insert("end", "-" * 20 + "\n", "标题")

    log = task["日志"]
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

    for title, content in log.items():
        log_text.insert("end", "========" + title + "========\n", "标题")
        for t, c in content.items():
            if t == "data" and c:
                if "level" in c[0].keys() and c[0]["level"] == "趣味拓展":
                    expand_conunt_text(c)
                else:
                    try:
                        level_conunt_text(c)
                    except KeyError:
                        log_text.insert("end", "数据" + "：" + str(c) + "\n")
            elif t == "state":
                log_text.insert("end", "结果" + "：" + state_str(c) + "\n", state_str(c))
            elif t == "message":
                log_text.insert("end", "信息：" + c + "\n")
            elif t == "file_count":
                log_text.insert("end", "文件数量（首页+趣味）" + "：" + str(c) + "\n")
            elif t == "random_file" and c:
                log_text.insert("end", "选取的国际化语言文件" + "：" + str(c) + "\n")

    log_text.configure(state="disabled")
