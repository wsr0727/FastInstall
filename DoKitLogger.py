import requests
import json
import time
import logging
import tkinter as tk
from tkinter import scrolledtext
import threading

logging.basicConfig(level=logging.INFO, format='')


"""查看iOS日志"""
timeStamp = 0  # 用于接口请求时间，接口返回结果是在这时间之后的日志
# filter_word = None  # 只展示含有这个关键字的日志
filter_word = ""
non_show_word = ""  # 不展示的日志
ip = "10.8.21.85:8888"  # ipad pro 尼克壳子
# ip = "10.8.27.204:8888"  # ipad pro 尼克壳子



'''
BBRest 休息
BBMathMainModule 思维主流程

'''


def print_log(text):
    # # =====开关控制是否过滤，不过滤就所有
    # if filter_word:
    #     if filter_word in str(text):
    #         logging.info(text['time'] + " 【TAG】" + text['logType'] + "：" + str(text['message']).strip())
    # elif non_show_word:
    #     if not text['logType'] == non_show_word:
    #         logging.info(text['time'] + " 【TAG】" + text['logType'] + "：" + str(text['message']).strip())
    # else:
    #     logging.info(text['time'] + " 【TAG】" + text['logType'] + "：" + str(text['message']).strip())

    # =====过滤休息计时，第三方广告日志
    if "BBRest" != text['logType'] and "BBThirdAD" != text['logType']:
        logging.info(text['time'] + " 【TAG】" + text['logType'] + "：" + str(text['message']).strip())
        log_to_text(text['time'] + " 【TAG】" + text['logType'] + "：" + str(text['message']).strip())
    # # =====测埋点专用
    # if "经分" in str(text) or "平台统计" in str(text):
    #     logging.info(text['time'] + " 【TAG】" + text['logType'] + "：" + str(text['message']).strip())


def get_log(ip):
    url = "http://" + ip + "/logs"
    body = {"timeStamp": str(timeStamp)}
    try:
        response = requests.request("POST", url, json=body)
        res = json.loads(response.text)
        return res["logs"]
    # except requests.exceptions.ConnectionError:
    except:
        return -1


def run():
    global timeStamp
    while True:
        log_list = get_log(ip)
        if log_list == -1:
            log_to_text(time.strftime("%Y-%m-%d %H:%M:%S") + " 【异常】应用未启动，或日志开关未开启")
        else:
            for i in reversed(log_list):  # 倒序读取日志列表
                print_log(i)
                timeStamp = i["timeStamp"]

        time.sleep(1)  # 暂停一秒


def thread_it(func, *args):
    """将函数打包进线程"""
    # 创建
    t = threading.Thread(target=func, args=args)
    # 守护
    t.setDaemon(True)
    # 启动
    t.start()


def highlight_keyword():
    # 清除之前的高亮
    log_text.tag_remove('highlight', '1.0', tk.END)
    keyword = search_entry.get()

    if keyword:
        start_idx = '1.0'
        while True:
            start_idx = log_text.search(keyword, start_idx, stopindex=tk.END)
            if not start_idx:
                break
            end_idx = f"{start_idx}+{len(keyword)}c"
            log_text.tag_add('highlight', start_idx, end_idx)
            start_idx = end_idx

        log_text.tag_config('highlight', background='yellow')


# 创建主窗口
root = tk.Tk()
root.title("日志展示框")

# 创建滚动文本区域用于显示日志
log_text = scrolledtext.ScrolledText(root, width=130, height=60)
log_text.grid(row=0, column=0)


# 将日志输出到文本区域
def log_to_text(message):
    log_text.insert(tk.END, message + '\n')
    # log_text.yview(tk.END)  # 自动滚动到底部

file_app_button = tk.Button(root, text="开始", width=15, command=lambda: thread_it(run))
file_app_button.grid(row=1, column=0, sticky="W")

search_entry = tk.Entry(root)
search_entry.grid(row=2, column=0, sticky="W")

search_button = tk.Button(root, text="Search", command=highlight_keyword)
search_button.grid(row=3, column=0, sticky="W")

# 运行主循环
root.mainloop()
