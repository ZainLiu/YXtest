from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.material_io.shema import *
from models import IsDelete, db, IsActive
from models.material_io import *
from utils.code_util import CodeUtil


class MaterialIoModule(ModuleBasic):

    @request_url(MaterialIOListSchema)
    def mt_io_get(self, form_data):
        filter_cond = [MaterialIORecord.type == form_data["type"]]
        if form_data.get("operate_type"):
            filter_cond.append(MaterialIORecord.operate_type == form_data.get("operate_type"))
        if form_data.get("serial_number"):
            filter_cond.append(MaterialIORecord.serial_number == form_data.get("serial_number"))
        if form_data.get("creator_name"):
            filter_cond.append(MaterialIORecord.creator_name.like(f'%{form_data["creator_name"]}%'))
        mt_io_record_set = MaterialIORecord.query.filter(*filter_cond).order_by(
            MaterialIORecord.id.desc()).paginate(form_data["page"], form_data["size"])
        resp_data = []
        for mt_io_record in mt_io_record_set.items:
            resp_data.append({
                "id": mt_io_record.id,
                "serial_number": mt_io_record.serial_number,
                "creator_id": mt_io_record.creator_id,
                "creator_name": mt_io_record.creator_name,
                "create_time": mt_io_record.create_time.strftime(current_app.config["APP_DATETIME_FORMAT"]),
                "mark": mt_io_record.mark,
                "operate_type": mt_io_record.operate_type
            })
        return self.report.table(resp_data, mt_io_record_set.total)

    @request_url(MaterialIODetailSchema)
    def mt_io_detail(self, form_data):
        mt_io_record = MaterialIORecord.query.filter_by(id=form_data["id"]).first()
        if not mt_io_record:
            return self.report.error("相关数据不存在")
        resp_data = {
            "id": mt_io_record.id,
            "serial_number": mt_io_record.serial_number,
            "creator_id": mt_io_record.creator_id,
            "creator_name": mt_io_record.creator_name,
            "detail_info": []
        }
        for detail in mt_io_record.mt_io_detail_set.all():
            detail_data = {
                "annex": detail.annex,
                "storehouse_name": detail.gsf.good_shelf.store_house.name,
                "material_type": CodeUtil.get_mc_full_name(detail.material.mc),
                "num": detail.num,
                "shelf_location": CodeUtil.get_gsf_full_name(detail.gsf),
                "material_name": detail.material.name,
                "material_brand": detail.material.brand.name,
                "material_model": detail.material.model,
                "material_specification": detail.material.specification,
                "material_entry_info": []
            }
            if mt_io_record.type == MaterialIOType.In:
                me_set = detail.mt_entry_in_set
            else:
                me_set = detail.mt_entry_out_set

            for me in me_set:
                detail_data["material_entry_info"].append({
                    "id": me.id,
                    "sn_no": me.sn_no,
                    "no": me.no,
                    "status": me.status,
                })

            resp_data["detail_info"].append(detail_data)
        return self.report.post(resp_data)


mt_io_module = MaterialIoModule()
