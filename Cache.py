import configparser
import logging
import os

"""
缓存相关代码
"""


def config_set(key_value):
    # key_value = {"key": {"app_key": "value"}} 参数格式
    # 初始化设置文件

    # 创建一个解析器对象
    cfg = configparser.ConfigParser()
    if not os.path.exists("FastInstall.config"):
        # 如果没有，创建一个新文件
        with open("FastInstall.config", "w") as f:
            # 向设置文件写入默认内容
            f.write("[app]" + "\n")
            f.write("app_key = com.sinyee.babybus.mathIII" + "\n")
            f.write("app_key_histroy = []" + "\n")
            f.write("[cache]" + "\n")
            f.write("input_histroy = []" + "\n")

    # 读取config文件的内容
    cfg.read("FastInstall.config")

    logging.debug("设置默认值：" + str(key_value))
    for i in key_value.keys():
        for j in key_value[i]:
            cfg.set(i, j, str(key_value[i][j]))

    # 保存修改
    with open("FastInstall.config", "w") as f:
        cfg.write(f)
        logging.debug("保存默认文件的修改")


def cache_set():
    # 初始化缓存数据
    if os.path.exists("FastInstall.config"):
        cfg = configparser.ConfigParser()
        cfg.read("FastInstall.config")
        app_key_get = cfg.get("app", "app_key")
        if not cfg.has_option("app", "app_key_histroy"):
            cfg["app"] = {"app_key": app_key_get, "app_key_histroy": []}
            with open("FastInstall.config", "w") as configfile:
                cfg.write(configfile)
        app_key_histroy_get = cfg.get("app", "app_key_histroy")
        if not cfg.has_option("cache", "input_histroy"):
            cfg.add_section("cache")
            cfg["cache"] = {"input_histroy": []}
            with open("FastInstall.config", "w") as configfile:
                cfg.write(configfile)
        input_list_get = cfg.get("cache", "input_histroy") if cfg.get("cache", "input_histroy") else "[]"
        return app_key_get, eval(input_list_get), eval(app_key_histroy_get)
    else:
        # app_key 默认为"com.sinyee.babybus.mathIII",app_key_histroy默认为[]，input_list默认为[]
        return "com.sinyee.babybus.mathIII", [], []


# app_key, input_list, app_key_histroy = cache_set()  # 初始化缓存
