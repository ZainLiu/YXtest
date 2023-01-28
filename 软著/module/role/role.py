from ly_kernel.Module import ModuleBasic
from flask import request
from utils.execl_read import ExeclReadService
from utils.execl_create import ExeclCreateService


class RoleModule(ModuleBasic):
    """角色相关操作"""

    def view(self):
        return self.report.post({"hello": "hello"})

    def add(self):
        file = request.files.get('file')
        data = ExeclReadService(file).read_execl('测试')

        # # 测试创建execl表
        # table_data = {
        #     '测试sheet':[
        #         ["id","姓名","性别","手机号"],
        #         [1.0,"姜子牙","男",1234567890.0],
        #         [2.0,"李绩","男",1234567891.0],
        #         [3.0,"诸葛亮","男",1234567892.0],
        #         [4.0,"孙武","男",1234567893.0],
        #         [5.0,"李靖","男",1234567894.0],
        #         [6.0,"张良","男",1234567895.0],
        #         [7.0,"吴起","男",1234567896.0],
        #         [8.0,"乐毅","男",1234567897.0],
        #         [9.0,"韩信","男",1234567898.0],
        #         [10.0,"白起","男",1234567899.0]
        #     ]
        # }
        # data = ExeclCreateService('测试').create_execl(table_data)

        return self.report.post({'data': data})


role_module = RoleModule()
