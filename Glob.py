class Glob:
    def __init__(self):
        self.gl_devices = []
        self.gl_app_key = []
        self.gl_app_key_histroy = []
        self.gl_input_list = []
        self.gl_task_list = []
        self.gl_ip_history = []

    def set_gl_devices(self, value):
        self.gl_devices = value

    def get_gl_devices(self):
        return self.gl_devices

    def set_gl_app_key(self, value):
        self.gl_app_key = value

    def get_gl_app_key(self):
        return self.gl_app_key

    def set_gl_app_key_histroy(self, value):
        self.gl_app_key_histroy = value

    def get_gl_app_key_histroy(self):
        return self.gl_app_key_histroy

    def set_gl_input_list(self, value):
        self.gl_input_list = value

    def get_gl_input_list(self):
        return self.gl_input_list

    def set_gl_task_list(self, value):
        self.gl_task_list = value

    def get_gl_task_list(self):
        return self.gl_task_list

    def set_gl_ip_history(self, value):
        self.gl_ip_history = value

    def get_gl_ip_history(self):
        return self.gl_ip_history


glob = Glob()

