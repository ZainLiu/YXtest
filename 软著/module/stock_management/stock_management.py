from flask import g
from ly_kernel.Module import ModuleBasic, request_url
from models import IsDelete, db, IsActive
from model_to_view.material.schema import MaterialListSchema
from model_to_view.stock_management.schema import StockManagementUpdateWarningNumSchema
from models import IsDelete, MaterialIOType
from models.material import Material
from utils.rpc_func import get_user_current_data_center_id


class StockManagementModule(ModuleBasic):

    @request_url(MaterialListSchema)
    def sm_list(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [Material.is_delete == IsDelete.NORMAL, Material.data_center_id == data_center_id]
        if form_data.get("mc_id"):
            filter_cond.append(Material.mc_id == form_data["mc_id"])
        if form_data.get("name"):
            filter_cond.append(Material.name.like(f"%{form_data['name']}%"))
        if form_data.get("brand_id"):
            filter_cond.append(Material.brand_id == form_data["brand_id"])
        if form_data.get("is_active") != None:
            filter_cond.append(Material.is_active == form_data["is_active"])
        if form_data.get("model"):
            filter_cond.append(Material.model == form_data["model"])
        mt_set = Material.query.filter(*filter_cond).order_by(Material.id.desc()).paginate(form_data["page"],
                                                                                           form_data["size"])
        resp_data = []
        for mt in mt_set.items:
            data = {
                "id": mt.id,
                "name": mt.name,
                "brand_id": mt.brand_id,
                "brand_name": mt.brand.name,
                "model": mt.model,
                "specification": mt.specification,
                "mark": mt.mark,
                "is_active": mt.is_active,
                "unit": mt.unit,
                "warning_num": mt.warning_num
            }
            stock_num = 0
            for mt_io_detail in mt.mt_io_detail_set:
                mt_io_record = mt_io_detail.mt_io_record
                if mt_io_record.type == MaterialIOType.In:
                    stock_num += mt_io_detail.num
                else:
                    stock_num -= mt_io_detail.num
            data["stock_num"] = stock_num
            resp_data.append(data)
        return self.report.table(resp_data, mt_set.total)

    @request_url(StockManagementUpdateWarningNumSchema)
    def sm_warning_num_update(self, form_data):
        mt = Material.query.filter_by(id=form_data["id"]).first()
        if not mt:
            return self.report.error("相关记录不存在")
        if form_data["warning_num"] < 0:
            return self.report.error("库存预警值不能小于0")
        mt.warning_num = form_data["warning_num"]
        db.session.add(mt)
        db.session.commit()
        return self.report.suc("修改成功")


sm_module = StockManagementModule()
