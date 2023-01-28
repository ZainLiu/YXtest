from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.brand.schema import *
from models import IsDelete, db
from models.brand import Brand


class BrandModule(ModuleBasic):

    @request_url(BrandCreateSchema)
    def create_br(self, form_data):
        old_recrod = Brand.query.filter_by(name=form_data["name"], is_delete=IsDelete.NORMAL).first()
        if old_recrod:
            return self.report.error("厂商名重复，禁止重复创建")
        br = Brand()
        br.name = form_data["name"]
        br.creator_name = g.account
        br.creator_id = g.uid
        db.session.add(br)
        db.session.commit()
        return self.report.suc("新增成功~")

    @request_url(BrandUpdateSchema)
    def update_br(self, form_data):
        br = Brand.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not br:
            return self.report.error("变更数据不存在")
        if br.name != form_data["name"]:
            old_recrod = Brand.query.filter_by(name=form_data["name"], is_delete=IsDelete.NORMAL).first()
            if old_recrod:
                return self.report.error("已存在相同名字的厂商，无法变更")
        br.name = form_data["name"]
        db.session.add(br)
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(BrandListSchema)
    def list_br(self, form_data):
        filter_cond = [Brand.is_delete == IsDelete.NORMAL]
        if form_data.get("name"):
            filter_cond.append(Brand.name.like(f"%{form_data['name']}%"))
        br_set = Brand.query.filter(*filter_cond).order_by(Brand.id.desc()).paginate(form_data["page"],
                                                                                     form_data["size"])
        resp_data = []
        for br in br_set.items:
            resp_data.append({
                "id": br.id,
                "name": br.name,
                "create_time": br.create_time.strftime(current_app.config["APP_DATETIME_FORMAT"]),
                "update_time": br.update_time.strftime(current_app.config["APP_DATETIME_FORMAT"])
            })
        return self.report.table(resp_data, br_set.total)

    @request_url(BrandDeleteSchema)
    def delete_br(self, form_data):
        br = Brand.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not br:
            return self.report.error("变更数据不存在")
        br.is_delete = IsDelete.Deleted
        db.session.add(br)
        db.session.commit()
        return self.report.suc("删除成功~")

    def list_br_simple(self):
        filter_cond = [Brand.is_delete == IsDelete.NORMAL]
        br_set = Brand.query.filter(*filter_cond).order_by(Brand.id.desc()).all()
        resp_data = []
        for br in br_set:
            resp_data.append({
                "id": br.id,
                "name": br.name,
            })
        return self.report.post(resp_data)


br_module = BrandModule()
