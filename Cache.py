import configparser
import logging
import os
import ast

"""
缓存相关代码
"""
config_path = "FastInstall.config"  # 缓存文件路径


def config_set(key_value):
    """
    设置缓存数据
    :param key_value: 需要写入的数据，参数格式:{"key": {"app_key": "value"}}
    :return:
    """
    cfg = configparser.ConfigParser()
    if not os.path.exists(config_path):
        # 如果文件不存在，创建一个新文件
        config_content = """\
        [app]
        app_key = com.sinyee.babybus.mathIII
        app_key_histroy = []
        [cache]
        input_histroy = []
        ip_history = []
        """

        with open(config_path, "w") as f:
            f.write(config_content)

    # 读取config文件的内容
    cfg.read(config_path)

    # 判断section
    if not cfg.has_section("cache"):
        cfg.add_section("cache")

    if not cfg.has_section("app"):
        cfg.add_section("app")

    logging.debug("设置默认值：" + str(key_value))
    for i, i_value in key_value.items():
        for j, j_value in i_value.items():
            cfg.set(i, j, str(j_value))

    # 保存修改
    with open(config_path, "w") as f:
        cfg.write(f)
        logging.debug("保存默认文件的修改")


def get_cache():
    """
    获取缓存数据
    :return: 返回获取到的值，或默认值
    """
    # 初始化缓存数据
    default_app_key = "com.sinyee.babybus.mathIII"
    default_app_key_history = []
    default_input_history = []
    default_ip_history = []

    cfg = configparser.ConfigParser()

    if os.path.exists(config_path):
        cfg.read(config_path)
    else:
        # 如果配置文件不存在，返回默认值
        return default_app_key, default_input_history, default_app_key_history, default_ip_history

    # 获取缓存
    app_key_get = cfg.get("app", "app_key", fallback=default_app_key)
    app_key_histroy_get = cfg.get("app", "app_key_histroy", fallback=str(default_app_key_history))
    input_histroy = cfg.get("cache", "input_histroy", fallback=str(default_input_history))
    ip_history = cfg.get("cache", "ip_history", fallback=str(default_ip_history))

    return app_key_get, ast.literal_eval(input_histroy), ast.literal_eval(app_key_histroy_get), ast.literal_eval(
        ip_history)

# app_key, input_list, app_key_histroy = cache_set()  # 初始化缓存
