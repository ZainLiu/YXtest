from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.supplier.schema import *
from models import IsDelete, db
from models.supplier import Supplier


class SupplierModule(ModuleBasic):
    @request_url(SupplierCreateSchema)
    def create_sp(self, form_data):
        old_recrod = Supplier.query.filter_by(name=form_data["name"], is_delete=IsDelete.NORMAL).first()
        if old_recrod:
            return self.report.error("厂商名重复，禁止重复创建")
        sp = Supplier()
        sp.name = form_data["name"]
        sp.mark = form_data["mark"]
        sp.contacts = form_data["contracts"]
        sp.creator_name = g.account
        sp.creator_id = g.uid
        db.session.add(sp)
        db.session.commit()
        return self.report.suc("新增成功~")

    @request_url(SupplierUpdateSchema)
    def update_sp(self, form_data):
        sp = Supplier.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not sp:
            return self.report.error("变更数据不存在")
        if sp.name != form_data["name"]:
            old_recrod = Supplier.query.filter_by(name=form_data["name"], is_delete=IsDelete.NORMAL).first()
            if old_recrod:
                return self.report.error("已存在相同名字的厂商，无法变更")
        sp.name = form_data["name"]
        sp.mark = form_data["mark"]
        sp.contacts = form_data["contracts"]
        db.session.add(sp)
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(SupplierListSchema)
    def list_sp(self, form_data):
        filter_cond = [Supplier.is_delete == IsDelete.NORMAL]
        if form_data.get("name"):
            filter_cond.append(Supplier.name.like(f"%{form_data['name']}%"))
        sp_set = Supplier.query.filter(*filter_cond).order_by(Supplier.id.desc()).paginate(form_data["page"],
                                                                                           form_data["size"])
        resp_data = []
        for sp in sp_set.items:
            resp_data.append({
                "id": sp.id,
                "name": sp.name,
                "mark": sp.mark,
                "contracts": sp.contacts,
                "create_time": sp.create_time.strftime(current_app.config["APP_DATETIME_FORMAT"]),
                "update_time": sp.update_time.strftime(current_app.config["APP_DATETIME_FORMAT"])
            })
        return self.report.table(resp_data, sp_set.total)

    @request_url(SupplierDeleteSchema)
    def delete_sp(self, form_data):
        sp = Supplier.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not sp:
            return self.report.error("变更数据不存在")
        sp.is_delete = IsDelete.Deleted
        db.session.add(sp)
        db.session.commit()
        return self.report.suc("删除成功~")

    def list_sp_simple(self):
        filter_cond = [Supplier.is_delete == IsDelete.NORMAL]

        sp_set = Supplier.query.filter(*filter_cond).order_by(Supplier.id.desc()).all()
        resp_data = []
        for sp in sp_set:
            resp_data.append({
                "id": sp.id,
                "name": sp.name,
            })
        return self.report.post(resp_data)


sp_module = SupplierModule()
