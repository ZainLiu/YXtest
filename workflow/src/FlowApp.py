import logging
import os
from ly_kernel.LieYing import LieYingApp

# 工作流系统

class FlowApp(LieYingApp):
    pass

    app_name = "workflowApp"
    app_name_cn = "工作流系统"
    app_blueprint_url = "/wkflow"

    app_root_path = os.path.join(os.path.dirname(__file__))

    def init_app(self):
        pass


flow_app = FlowApp(__name__)

if __name__ == '__main__':
    flow_app.run_app()
