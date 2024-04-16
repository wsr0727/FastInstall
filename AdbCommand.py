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
    command = 'adb -s ' + device + ' shell input text ' + text
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
        logging.info("【安装成功】:" + log_info)
        return list(install_appkey), True
    else:
        logging.error("【安装失败】: adb命令：" + install_command + "  原因:\n" + install_result)


def get_packages_list(device):
    # 获取当前设备安装的应用
    packages_list_command = os.popen("adb -s " + device + " shell pm list packages -3").readlines()
    packages_list = [packages.split(":")[-1].splitlines()[0] for packages in packages_list_command]
    return packages_list


def get_adress(adress):
    adress_list = []
    logging.debug("正在处理的目录：" + adress)
    if os.path.isdir(adress):
        for f in os.listdir(adress):
            # 只装apk
            if ".apk" in f or ".ipa" in f or ".aab" in f or ".json" in f:
                adress_list.append('{}/{}'.format(adress, f))
    else:
        adress_list = [item for item in adress.split("\n") if
                       ".apk" in item or ".ipa" in item or ".aab" in item or ".json" in item]
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
    # 启动应用
    logging.debug("【正在启动应用】：" + package_name)
    os.popen("adb -s " + device + " shell am start " + package_name + "/com.sinyee.babybus.SplashAct").read()
    time.sleep(2)

    # 点击政策，没有也会点 不管成功失败
    screen_size = os.popen("adb -s " + device + " shell wm size").read()
    y, x = screen_size.split(":")[-1].strip().split("x")
    click_y = str(int(int(y) / 2 + 365))
    click_x = str(int(int(x) / 2))  # 居中的位置
    os.popen("adb -s " + device + " shell input touchscreen tap " + click_x + " " + click_y).read()  # 同意政策
    time.sleep(1)
    click_y_2 = str(int(int(y) / 2 + 350))
    os.popen("adb -s " + device + " shell input touchscreen tap " + click_x + " " + click_y_2).read()  # 同意隐私弹框

    # 开场动画
    time.sleep(15)


def open_app(device, package_name):
    # 启动应用
    logging.debug("【正在启动应用】：" + package_name)
    os.popen("adb -s " + device + " shell am start " + package_name + "/com.sinyee.babybus.SplashAct").read()


def release_debug(device, close=False):
    if not close:
        logging.debug("【开启正式线调试指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybus.app all").read()
    else:
        logging.debug("【关闭正式线调试指令】：" + device)
        os.popen("adb -s " + device + " shell setprop debug.babybus.app none.").read()


def ad_debug(device, close=False):
    if not close:
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
    :param device:
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
