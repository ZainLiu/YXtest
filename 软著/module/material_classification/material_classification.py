from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.material_classification.schema import *
from models import IsDelete, db, IsActive, YesOrNo
from models.material_classification import MaterialClassification


class MaterialClassificationModule(ModuleBasic):
    @request_url(MaterialClassificationCreateSchema)
    def create_sub_mc(self, form_data):
        parent = MaterialClassification.query.filter_by(id=form_data['parent_id']).first()
        if not parent:
            return self.report.error("父分类不存在")
        old_record = MaterialClassification.query.filter_by(parent_id=parent.id,
                                                            name=form_data["name"], is_delete=IsDelete.NORMAL).all()
        if old_record:
            return self.report.error("该分类下已有相同名称子分类")

        mc = MaterialClassification()
        mc.name = form_data["name"]
        mc.introduction = form_data["introduction"]
        mc.parent_id = parent.id
        mc.creator_id = g.uid
        mc.creator_name = g.account
        db.session.add(mc)
        db.session.commit()
        return self.report.suc("创建成功")

    @request_url(MaterialClassificationUpdateSchema)
    def update_sub_mc(self, form_data):
        mc = MaterialClassification.query.filter_by(id=form_data["id"]).first()
        if not mc:
            return self.report.error("相关记录不存在")
        if mc.name != form_data["name"]:
            old_record = MaterialClassification.query.filter_by(parent_id=mc.parent_id,
                                                                name=form_data["name"],
                                                                is_delete=IsDelete.NORMAL).first()

            if old_record:
                return self.report.error("该分类下已有同名子分类，禁止修改")
        mc.name = form_data["name"]
        mc.introduction = form_data["introduction"]
        db.session.add(mc)
        db.session.commit()
        return self.report.suc("更新成功")

    def get_sub_mc_info(self, parent_id, mc_set):
        sub_mc_set = [sub_mc for sub_mc in mc_set if sub_mc.parent_id == parent_id]
        if not sub_mc_set:
            return []
        else:
            sub_mc_info = []
            for sub_mc in sub_mc_set:
                sub_mc_info.append({
                    "id": sub_mc.id,
                    "name": sub_mc.name,
                    "is_active": sub_mc.is_active,
                    "sub_mc_info": self.get_sub_mc_info(sub_mc.id, mc_set),
                    "introduction": sub_mc.introduction
                })
            return sub_mc_info

    def list_sub_mc(self):
        mc_set = MaterialClassification.query.filter_by(is_delete=IsDelete.NORMAL).all()
        top_set = [mc for mc in mc_set if mc.parent_id is None]
        resp_data = []
        for top in top_set:
            resp_data.append({
                "id": top.id,
                "name": top.name,
                "is_active": top.is_active,
                "sub_mc_info": self.get_sub_mc_info(top.id, mc_set),
                "introduction": top.introduction
            })
        return self.report.post(resp_data)

    def get_sub_mc_info_simple(self, parent_id, mc_set):
        sub_mc_set = [sub_mc for sub_mc in mc_set if
                      sub_mc.parent_id == parent_id and sub_mc.is_active == YesOrNo.YES]
        if not sub_mc_set:
            return []
        else:
            sub_mc_info = []
            for sub_mc in sub_mc_set:
                sub_mc_info.append({
                    "id": sub_mc.id,
                    "name": sub_mc.name,
                    "sub_mc_info": self.get_sub_mc_info(sub_mc.id, mc_set)
                })
            return sub_mc_info

    def list_sub_mc_simple(self):
        mc_set = MaterialClassification.query.filter_by(is_delete=IsDelete.NORMAL, is_active=YesOrNo.YES).all()
        top_set = [mc for mc in mc_set if mc.parent_id is None]
        resp_data = []
        for top in top_set:
            resp_data.append({
                "id": top.id,
                "name": top.name,
                "sub_mc_info": self.get_sub_mc_info_simple(top.id, mc_set)
            })
        return self.report.post(resp_data)

    def disable_sub_mc(self, mc, status):
        if not mc.sub_mf_set:
            return
        for sub_mc in mc.sub_mf_set:
            sub_mc.is_active = status
            db.session.add(sub_mc)
            self.disable_sub_mc(sub_mc, status)

    def mc_status_switch(self, mc, status):
        try:
            self.disable_sub_mc(mc, status)
            mc.is_active = status
            db.session.add(mc)
        except Exception as e:
            db.session.rollback()
            return False, str(e)
        db.session.commit()
        return True, "操作成功"

    @request_url(MaterialClassificationStatusSwitchSchema)
    def mc_active(self, form_data):
        mc = MaterialClassification.query.filter_by(id=form_data["id"]).first()
        if not mc:
            return self.report.error("相关数据不存在")
        if mc.parent:
            if mc.parent.is_active == IsActive.Disable:
                return self.report.error("父类正在停用，不能启用")
        status, msg = self.mc_status_switch(mc, YesOrNo.YES)
        if not status:
            return self.report.error(msg)
        return self.report.suc("激活成功")

    @request_url(MaterialClassificationStatusSwitchSchema)
    def mc_disable(self, form_data):
        mc = MaterialClassification.query.filter_by(id=form_data["id"]).first()
        if not mc:
            return self.report.error("相关数据不存在")
        status, msg = self.mc_status_switch(mc, YesOrNo.NO)
        if not status:
            return self.report.error(msg)
        return self.report.suc("停用成功")


mc_module = MaterialClassificationModule()
