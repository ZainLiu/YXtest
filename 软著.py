import datetime
import os

import docx


def walkFile(file, doc):
    for root, dirs, files in os.walk(file):

        # root 表示当前正在访问的文件夹路径

        # dirs 表示该文件夹下的子目录名list

        # files 表示该文件夹下的文件list

        # 遍历文件

        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                with open(os.path.join(root, f), "r", encoding="utf8") as f:
                    data = f.read()
                    doc.add_paragraph(data)

        # 遍历所有的文件夹

        for d in dirs:
            walkFile(d, doc)



if __name__ == '__main__':
    doc = docx.Document()
    # 变更管理
    # walkFile("../models/change", doc)
    # walkFile("../models/change_admin", doc)
    # walkFile("../module/change_programme", doc)
    # walkFile("../module/change_admin_apply", doc)
    # walkFile("../module/change_admin_programme", doc)
    # walkFile("../module/change_admin_task", doc)
    # doc.save(f"./data/DCOS变更管理软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")
    # walkFile("../module/cs_work_order", doc)
    # walkFile("../module/statistical_analysis", doc)
    # walkFile("../module/storehouse", doc)
    # walkFile("../module/standard_job_procedures", doc)
    # walkFile("../module/standard_job_classification", doc)
    # 客服工单
    # walkFile("../models/service_manage/work_order_manage", doc)
    # walkFile("../module/cs_work_order", doc)
    # walkFile("../module/cs_work_order_type", doc)
    # walkFile("../cs_work_order_type", doc)
    # doc.save(f"./data/DCOS客服工单软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")

    # 库存管理
    # walkFile("../module/stock_management", doc)
    # walkFile("../module/storehouse", doc)
    # walkFile("../module/material", doc)
    # walkFile("../module/material_io", doc)
    # walkFile("../module/material_classification", doc)
    # doc.save(f"./data/DCOS库存管理软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")

    # 统计分析
    # walkFile("../module/statistical_analysis", doc)
    # walkFile("../module/cockpit", doc)
    #
    # doc.save(f"./data/DCOS统计分析软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")

    # 资料库
    # walkFile("../module/standard_job_procedures", doc)
    # walkFile("../module/standard_job_classification", doc)
    #
    # doc.save(f"./data/DCOS资料库软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")

    # 排班管理
    # walkFile("../module/rostering_work_rule", doc)
    # walkFile("../module/rostering_work_type", doc)
    # walkFile("../module/rostering_work_admin", doc)
    # walkFile("../module/rostering_work_panel", doc)
    # walkFile("../module/rostering_work_change", doc)
    # walkFile("../module/rostering_people_group", doc)
    # walkFile("../module/rostering_work_exchange", doc)
    # walkFile("../module/rostering_work_handover", doc)
    #
    # doc.save(f"./data/DCOS排班管理软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")

    # 服务资产管理
    # walkFile("../module/cabinet_management", doc)
    # walkFile("../model_to_view/cabinet_management", doc)
    # walkFile("../models/material_classification.py", doc)
    # doc.save(f"./data/DCOS服务资产管理软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")

    # 客户资产管理
    walkFile("./asynicio_test",doc)
    walkFile("./flask_sse_v1",doc)
    walkFile("./flask微服务",doc)
    walkFile("./kafka_test",doc)
    walkFile("./myserver",doc)
    walkFile("./pytorch_practice",doc)
    walkFile("./redis相关",doc)
    walkFile("./tenserflow_test",doc)

    doc.save(f"./DCOSk客户资产管理软著代码{datetime.datetime.today().strftime('%Y-%m-%d')}.docx")




