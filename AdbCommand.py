import os
import time
import logging

"""
ADB相关指令
"""

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s: [%(funcName)s] %(message)s')


def get_devices_all():
    # 获取devices数量和名称
    devices = []  # 每次都重置设备列表
    for dName_ in os.popen('adb devices -l'):
        if "List of devices attached" not in dName_:
            name_list = dName_.split()
            if "device" in name_list:  # 只加入成功连接的设备
                devices.append([name_list[0], name_list[3].strip("model:")])
    return devices


# 输入指定字符
def input_text(device, text):

    text = text.replace('"', '\\"') if '"' in text else text
    text = text.strip().rstrip()
    command = 'adb -s ' + device + ' shell input text ' + f"'{text}'"
    os.popen(command).read()


# 安装app
def adb_install(device, adress):
    install_last = get_packages_list(device)
    log_info = '设备：' + str(device) + '； ' + '文件：' + adress
    logging.debug("【正在安装】:" + log_info)
    install_command = 'adb -s ' + str(device) + ' install ' + '"{}"'.format(str(adress))
    install_result_str = os.popen(str(install_command))
    install_result = install_result_str.buffer.read().decode(encoding='utf-8')
    time.sleep(1)
    if 'Success' in install_result:
        install_after = get_packages_list(device)
        install_appkey = set(install_last) ^ set(install_after)
        logging.debug("【安装成功】:" + log_info)
        return list(install_appkey), True
    else:
        logging.error("【安装失败】: adb命令：" + install_command + "  原因:\n" + install_result)


def get_packages_list(device):
    # 获取当前设备安装的应用
    packages_list_command = os.popen("adb -s " + device + " shell pm list packages -3").readlines()
    packages_list = [packages.split(":")[-1].splitlines()[0] for packages in packages_list_command]
    return packages_list


def get_adress(adress):
    logging.debug("正在处理的目录：" + adress)
    extensions = ['.apk', '.ipa', '.aab','hap', '.json']  # 只读取这些文件类型的路径
    if os.path.isdir(adress):
        adress_list = ['{}/{}'.format(adress, f) for f in os.listdir(adress) if any(ext in f for ext in extensions)]
    else:
        adress_list = [item for item in adress.split("\n") if any(ext in item for ext in extensions)]
    return adress_list


# 卸载手机上所有应用
def uninstall(device, package_name):
    uninstall_command = os.popen('adb -s ' + device + " uninstall " + package_name).read()
    log_info = '包名：' + package_name + '  设备：' + str(device)
    if 'Success' in uninstall_command[-9:]:
        logging.info("【删除成功】：" + log_info)
        return True
    else:
        logging.error("【删除失败】" + log_info + "\n原因:\n" + uninstall_command)
        return False


def luncher_app(device, package_name):
    """"
    专门用于批量安装应用，流程包含启动-点击隐私政策-点击权限弹框。只点击不判断是否成功
    :param device: 设备标识
    :param package_name: 应用key
    :return:
    """
    # 启动应用
    logging.debug("【正在启动应用】：" + package_name)
    open_app(device, package_name)
    time.sleep(2)

    # 点击政策，没有也会点 不管成功失败
    y, x = get_screen_size(device)
    click_y = int(y / 2)
    click_x = str(int(x / 2))  # 居中的位置
    os.popen(
        "adb -s " + device + " shell input touchscreen tap " + click_x + " " + str(click_y + 365)).read()  # 同意政策
    time.sleep(1)
    os.popen(
        "adb -s " + device + " shell input touchscreen tap " + click_x + " " + str(click_y + 350)).read()  # 同意隐私弹框

    time.sleep(15)
    os.popen("adb -s " + device + " shell input touchscreen tap " + click_x + " " + str(click_y)).read()  # 选择阶段
    os.popen("adb -s " + device + " shell input touchscreen tap " + click_x + " " + str(click_y)).read()  # 选择阶段

    # 开场动画
    time.sleep(5)


def get_screen_size(device):
    """"
    获取设备分辨率
    :param device: 设备标识
    :return: y=宽, x=高
    """
    screen_size = os.popen("adb -s " + device + " shell wm size").read()
    y, x = screen_size.split(":")[-1].strip().split("x")
    return int(y), int(x)


def open_app(device, app_name):
    # 启动应用
    def lunch_(lunch_device, activity):
        return os.popen(f"adb -s {lunch_device} shell am start -W {activity}").read().split("\n")

    if "com.sinyee.babybus" in app_name:
        logging.debug("【正在启动宝宝巴士应用】：" + app_name)
        line = app_name + "/com.sinyee.babybus.SplashAct"
    else:
        line = app_name
        logging.debug("【正在启动链接】：" + app_name)

    adb_log = lunch_(device, line)
    if 'Error type 3' in adb_log:
        # 兼容新旧两种activity
        adb_log = lunch_(device, app_name + "/com.babybus.math.plugin.main.activity.SplashAct")

    info = {key: next((line.split(":")[-1].strip() for line in adb_log if key in line), '') for key in
            ['LaunchState', 'TotalTime', 'WaitTime']}
    logging.debug("【启动时长】：" + str(info))
    return info


def release_debug(device, status=True):
    """
    开启正式线调试
    :param device: 设备ID
    :param status: 是否开启，True 开 ，False 关
    :return:
    """
    if status:
        logging.debug("【开启正式线调试指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybus.app all").read()
    else:
        logging.debug("【关闭正式线调试指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybus.app none.").read()


def setting_resolution(device, resolution_list):
    """
    设置设备分辨率
    :param device: 设备ID
    :param resolution_list: resolution_list[0]: status 是否已设置分辨率，True 开 ，False 关
                            resolution_list[1]: width 输入框填写的宽
                            resolution_list[2]: height 输入框填写的高
    """

    # 获取当前设备最大分辨率
    width_max, height_max = get_screen_size(device)
    status = resolution_list[0]
    if status:
        try:
            width = int(resolution_list[1].get())
            height = int(resolution_list[2].get())

            # 检查是否在指定范围内
            if 0 < width <= width_max and 0 < height <= height_max:
                resolution = f"{width}x{height}"
                logging.debug(f"【设置分辨率】：{resolution}")
                os.popen(f"adb -s {device} shell wm size {resolution}").read()
            else:
                logging.debug("请检查分辨率设置：分辨率超出允许范围。")

        except ValueError:
            logging.debug("请输入有效的数字作为宽度和高度。")

    else:
        logging.debug("【恢复分辨率】：" + device)
        os.popen("adb -s " + device + " shell wm size reset").read()


def ad_debug(device, status=True):
    """
    开启正式线广告调试
    :param device: 设备ID
    :param status: 是否开启，True 开 ，False 关
    :return:
    """
    if status:
        logging.debug("【开启正式线广告日志指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybusadenablelog 1").read()
    else:
        logging.debug("【关闭正式线广告日志指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybusadenablelog none.").read()


def clear_app(device, app_key):
    logging.debug("【清空应用缓存】：" + device)
    os.popen("adb -s " + device + " shell pm clear " + app_key).read()


def setting_debug(device, page="语言"):
    """
    打开设置页面
    :param device: 设备标识
    :param page: 支持“语言”、“时间”、“WiFi”
    :return:
    """
    logging.debug("【开启" + page + "设置】：" + device)
    if page == "语言":
        os.popen("adb -s " + device + " shell am start -a android.settings.LOCALE_SETTINGS").read()
    elif page == "时间":
        os.popen("adb -s " + device + " shell am start -a android.settings.DATE_SETTINGS").read()
    elif page == "WiFi":
        os.popen("adb -s " + device + " shell am start -a android.settings.WIFI_SETTINGS").read()


def wifi_proxy_setting(device, ip="", port="0", status=True):
    """
    设置WiFi代理
    :param device: 设备标识
    :param ip: 代理IP
    :param port: 代理端口
    :param status: 是否开启，True 开 ，False 关
    :return: 指令是否执行成功。
    """

    if status:
        logging.debug("【开启全局WIFI代理】：" + device + " [ip]" + ip + ":" + port)
    else:
        ip, port = "", "0"
        logging.debug("【关闭全局WIFI代理】：" + device)
    os.popen("adb -s " + device + " shell settings put global http_proxy " + ip + ":" + port).read()

    return wifi_proxy_check(device)["info"] == ip + ":" + port


def wifi_proxy_check(device):
    """
    判断当前设备是否有开启全局wifi代理
    :param device: 设备标识
    :return: 返回当前代理是否开启（true 开，false 关），info具体信息
    """
    info = os.popen("adb -s " + device + " shell settings get global http_proxy").read().strip()
    logging.debug("【WIFI代理结果】：" + device + " [ip]" + info)
    return {"state": info not in ["null", ":0"], "info": info}
