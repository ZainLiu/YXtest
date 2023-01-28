from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.material.schema import *
from models.brand import Brand
from models.data_center import DataCenter
from models.material import Material
from models import *
from models.storehouse import GoodShelfFloor
from utils.code_util import CodeUtil
from utils.rpc_func import get_user_current_data_center_id


class MaterialModule(ModuleBasic):

    @request_url(MaterialCreateSchema)
    def create_mt(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        data_center = DataCenter.query.filter_by(id=data_center_id).first()
        if not data_center:
            return self.report.error("数据中心不存在")
        brand = Brand.query.filter_by(id=form_data["brand_id"]).first()
        if not brand:
            return self.report.error("品牌不存在")
        mt = Material()
        mt.name = form_data["name"]
        mt.brand_id = brand.id
        mt.data_center_id = data_center.id
        mt.unit = form_data["unit"]
        mt.model = form_data["model"]
        mt.mc_id = form_data["mc_id"]
        mt.specification = form_data["specification"]
        mt.mark = form_data["mark"]
        mt.creator_id = g.uid
        mt.creator_name = g.account
        db.session.add(mt)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(MaterialUpdateSchema)
    def update_mt(self, form_data):
        mt = Material.query.filter_by(id=form_data["id"]).first()
        if not mt:
            return self.report.error("相关数据不存在")
        brand = Brand.query.filter_by(id=form_data["brand_id"]).first()
        if not brand:
            return self.report.error("品牌不存在")
        mt.name = form_data["name"]
        mt.brand_id = brand.id
        mt.unit = form_data["unit"]
        mt.model = form_data["model"]
        mt.specification = form_data["specification"]
        mt.mark = form_data["mark"]

        db.session.add(mt)
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(MaterialListSchema)
    def list_mt(self, form_data):
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
        mt_set = Material.query.filter(*filter_cond).order_by(Material.id.desc()).paginate(form_data["page"],
                                                                                           form_data["size"])
        resp_data = []
        for mt in mt_set.items:
            resp_data.append({
                "id": mt.id,
                "name": mt.name,
                "brand_id": mt.brand_id,
                "brand_name": mt.brand.name,
                "model": mt.model,
                "specification": mt.specification,
                "mark": mt.mark,
                "is_active": mt.is_active,
                "unit": mt.unit,
            })
        return self.report.table(resp_data, mt_set.total)

    @request_url(MaterialDetailSchema)
    def detail_mt(self, form_data):
        mt = Material.query.filter_by(id=form_data["id"]).first()
        if not mt:
            return self.report.error("相关数据不存在")
        resp_data = {
            "id": mt.id,
            "name": mt.name,
            "mc_id": mt.mc_id,
            "mc_name": mt.mc.name,
            "specification": mt.specification,
            "is_active": mt.is_active,
            "mark": mt.mark,
            "brand_id": mt.brand_id,
            "brand_name": mt.brand.id,
            "model": mt.model,
            "unit": mt.unit,
            "mt_io_info": [],
            "stock_info": []
        }
        # 物资出入库记录
        gsf_stock_info = dict()
        for mt_io_detail in mt.mt_io_detail_set:
            mt_io_record = mt_io_detail.mt_io_record
            num = gsf_stock_info.get(mt_io_detail.gsf_id, 0)
            if mt_io_record.type == MaterialIOType.In:
                num += mt_io_detail.num
            else:
                num -= mt_io_detail.num
            gsf_stock_info[mt_io_detail.gsf_id] = num
            resp_data["mt_io_info"].append({
                "create_time": mt_io_record.create_time.strftime(current_app.config['APP_DATE_FORMAT']),
                "type": mt_io_record.type,
                "operate_type": mt_io_record.operate_type,
                "serial_number": mt_io_record.serial_number,
                "num": mt_io_detail.num,
                "creator_name": mt_io_record.creator_name
            })
        # 库存列表
        gsf_set = GoodShelfFloor.query.filter(GoodShelfFloor.id.in_(gsf_stock_info.keys())).all()
        for gsf in gsf_set:
            if gsf_stock_info[gsf.id] == 0:
                continue
            resp_data["stock_info"].append({
                "location": CodeUtil.get_gsf_full_name(gsf),
                "storehouse_name": gsf.good_shelf.store_house.name,
                "num": gsf_stock_info[gsf.id],
                "unit": mt.unit
            })
        return self.report.post(resp_data)

    @staticmethod
    def mt_status_switch(mt, status):
        mt.is_active = status
        db.session.add(mt)
        db.session.commit()

    @request_url(MaterialStatusSwitchSchema)
    def disable_mt(self, form_data):
        mt = Material.query.filter_by(id=form_data["id"]).first()
        if not mt:
            return self.report.error("相关数据不存在")
        self.mt_status_switch(mt, IsActive.Disable)
        return self.report.suc("停用成功")

    @request_url(MaterialStatusSwitchSchema)
    def active_mt(self, form_data):
        mt = Material.query.filter_by(id=form_data["id"]).first()
        if not mt:
            return self.report.error("相关数据不存在")
        self.mt_status_switch(mt, IsActive.Active)
        return self.report.suc("激活成功")


mt_module = MaterialModule()
