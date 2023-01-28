from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.manufacturer.schema import *
from models import IsDelete, db, EquipmentStatus
from models.equipment import Equipment
from models.manufacturer import Manufacturer


class ManufacturerModule(ModuleBasic):

    @request_url(ManufacturerCreateSchema)
    def create_mf(self, form_data):
        old_recrod = Manufacturer.query.filter_by(name=form_data["name"], is_delete=IsDelete.NORMAL).first()
        if old_recrod:
            return self.report.error("厂商名重复，禁止重复创建")
        mf = Manufacturer()
        mf.name = form_data["name"]
        mf.mark = form_data["mark"]
        mf.contacts = form_data["contracts"]
        mf.creator_name = g.account
        mf.creator_id = g.uid
        db.session.add(mf)
        db.session.commit()
        return self.report.suc("新增成功~")

    @request_url(ManufacturerUpdateSchema)
    def update_mf(self, form_data):
        mf = Manufacturer.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not mf:
            return self.report.error("变更数据不存在")
        if mf.name != form_data["name"]:
            old_recrod = Manufacturer.query.filter_by(name=form_data["name"], is_delete=IsDelete.NORMAL).first()
            if old_recrod:
                return self.report.error("已存在相同名字的厂商，无法变更")
        mf.name = form_data["name"]
        mf.mark = form_data["mark"]
        mf.contacts = form_data["contracts"]
        db.session.add(mf)
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(ManufacturerListSchema)
    def list_mf(self, form_data):
        filter_cond = [Manufacturer.is_delete == IsDelete.NORMAL]
        if form_data.get("name"):
            filter_cond.append(Manufacturer.name.like(f"%{form_data['name']}%"))
        mf_set = Manufacturer.query.filter(*filter_cond).order_by(Manufacturer.id.desc()).paginate(form_data["page"],
                                                                                                   form_data["size"])
        resp_data = []
        for mf in mf_set.items:
            resp_data.append({
                "id": mf.id,
                "name": mf.name,
                "mark": mf.mark,
                "contracts": mf.contacts,
                "create_time": mf.create_time.strftime(current_app.config["APP_DATETIME_FORMAT"]),
                "update_time": mf.update_time.strftime(current_app.config["APP_DATETIME_FORMAT"])
            })
        return self.report.table(resp_data, mf_set.total)

    @request_url(ManufacturerDeleteSchema)
    def delete_mf(self, form_data):
        mf = Manufacturer.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not mf:
            return self.report.error("变更数据不存在")
        mf.is_delete = IsDelete.Deleted
        db.session.add(mf)
        db.session.commit()
        return self.report.suc("删除成功~")

    def list_mf_simple(self):
        filter_cond = [Manufacturer.is_delete == IsDelete.NORMAL]
        mf_set = Manufacturer.query.filter(*filter_cond).order_by(Manufacturer.id.desc()).all()
        resp_data = []
        for mf in mf_set:
            resp_data.append({
                "id": mf.id,
                "name": mf.name,
            })
        return self.report.post(resp_data)

    @request_url(ManufacturerListByEqModelSchema)
    def mf_list_by_eq_model(self, form_data):
        eq_set = Equipment.query.filter_by(equipment_model=form_data["eq_model"], status=EquipmentStatus.Using,
                                           is_delete=IsDelete.NORMAL).all()
        mf_set = Manufacturer.query.filter(Manufacturer.id.in_([eq.manufacturer_id for eq in eq_set])).all()
        resp_data = []
        for mf in mf_set:
            resp_data.append({
                "id": mf.id,
                "name": mf.name,
            })

        return self.report.post(resp_data)


mf_module = ManufacturerModule()
