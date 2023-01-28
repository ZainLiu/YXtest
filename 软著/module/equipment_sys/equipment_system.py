from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.equipment_sys.equipment_system import *
from models import IsDelete, db, YesOrNo, IsActive, EquipmentStatus
from models.equipment import EquipmentSystem, EquipmentSubSystem, EquipmentType, Equipment
from utils.rpc_func import get_user_current_data_center_id


class EquipmentSysTem(ModuleBasic):

    @request_url(EquipmentSystemListViewSchema)
    def eq_sys_list(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        eq_sys_set = EquipmentSystem.query.filter_by(data_center_id=data_center_id).all()
        resp_data = []
        for eq_sys in eq_sys_set:
            resp_data.append({
                "id": eq_sys.id,
                "name": eq_sys.name,
                "code": eq_sys.code
            })
        return self.report.post(resp_data)

    @request_url(EquipmentSystemListViewSchema)
    def eq_sys_list_all(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        eq_sys_set = EquipmentSystem.query.filter_by(data_center_id=data_center_id).all()
        resp_data = []
        for eq_sys in eq_sys_set:
            eq_sys_info = {
                "id": eq_sys.id,
                "name": eq_sys.name,
                "code": eq_sys.code,
                "eq_sub_sys_info": []
            }
            for eq_sub_sys in eq_sys.eq_sub_sys_set.filter_by(is_delete=IsDelete.NORMAL,
                                                              is_active=YesOrNo.YES).all():
                eq_sub_sys_info = {
                    "id": eq_sub_sys.id,
                    "name": eq_sub_sys.name,
                    "code": eq_sub_sys.code,
                    "eq_type_info": []
                }
                for eq_type in eq_sub_sys.equipment_type_set.filter_by(is_delete=IsDelete.NORMAL,
                                                                       is_active=YesOrNo.YES).all():
                    eq_type_info = {
                        "id": eq_type.id,
                        "name": eq_type.name,
                        "code": eq_type.code,
                        "extra_field": eq_type.extra_field
                    }
                    eq_sub_sys_info["eq_type_info"].append(eq_type_info)
                eq_sys_info["eq_sub_sys_info"].append(eq_sub_sys_info)
            resp_data.append(eq_sys_info)
        return self.report.post(resp_data)

    def get_eq_model_set(self, data_center_id):
        data = dict()
        eq_set = Equipment.query.filter_by(data_center_id=data_center_id, status=EquipmentStatus.Using).all()
        for eq in eq_set:
            if data.get(eq.equipment_type_id):
                data[eq.equipment_type_id].add(eq.equipment_model)
            else:
                model_set = set()
                model_set.add(eq.equipment_model)
                data[eq.equipment_type_id] = model_set
        return data

    def eq_sys_list_all_with_eq_model(self):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        eq_model_set = self.get_eq_model_set(data_center_id)
        eq_sys_set = EquipmentSystem.query.filter_by(data_center_id=data_center_id).all()
        resp_data = []
        for eq_sys in eq_sys_set:
            eq_sys_info = {
                "id": eq_sys.id,
                "name": eq_sys.name,
                "code": eq_sys.code,
                "eq_sub_sys_info": []
            }
            for eq_sub_sys in eq_sys.eq_sub_sys_set.filter_by(is_delete=IsDelete.NORMAL,
                                                              is_active=YesOrNo.YES).all():
                eq_sub_sys_info = {
                    "id": eq_sub_sys.id,
                    "name": eq_sub_sys.name,
                    "code": eq_sub_sys.code,
                    "eq_type_info": []
                }
                for eq_type in eq_sub_sys.equipment_type_set.filter_by(is_delete=IsDelete.NORMAL,
                                                                       is_active=YesOrNo.YES).all():
                    eq_type_info = {
                        "id": eq_type.id,
                        "name": eq_type.name,
                        "code": eq_type.code,
                        "eq_model_info": list(eq_model_set.get(eq_type.id, set()))
                    }
                    eq_sub_sys_info["eq_type_info"].append(eq_type_info)
                eq_sys_info["eq_sub_sys_info"].append(eq_sub_sys_info)
            resp_data.append(eq_sys_info)
        return self.report.post(resp_data)

    @request_url(EquipmentSubSystemListViewSchema)
    def eq_sub_sys_list(self, form_data):
        eq_sub_sys_set = EquipmentSubSystem.query.filter_by(equipment_system_id=form_data["eq_sys_id"]).all()
        resp_data = []
        for eq_sub_sys in eq_sub_sys_set:
            resp_data.append({
                "id": eq_sub_sys.id,
                "name": eq_sub_sys.name,
                "code": eq_sub_sys.code,
                "is_active": eq_sub_sys.is_active,
                "is_sys_conf": eq_sub_sys.is_sys_conf,
                "introduction": eq_sub_sys.introduction
            })
        return self.report.post(resp_data)

    @request_url(EquipmentSubSystemListViewSchema)
    def eq_sub_sys_list_simple(self, form_data):
        eq_sub_sys_set = EquipmentSubSystem.query.filter_by(equipment_system_id=form_data["eq_sys_id"],
                                                            is_active=YesOrNo.YES).all()
        resp_data = []
        for eq_sub_sys in eq_sub_sys_set:
            resp_data.append({
                "id": eq_sub_sys.id,
                "name": eq_sub_sys.name,
            })
        return self.report.post(resp_data)

    def get_eq_sub_sys_list(self):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        resp_data = []
        es_set = EquipmentSystem.query.filter_by(data_center_id=dc_id).all()
        for es in es_set:
            es_info = {
                "id": es.id,
                "name": es.name,
                "code": es.code,
                "eq_sub_sys_info": []
            }
            for ess in es.eq_sub_sys_set.all():
                es_info["eq_sub_sys_info"].append({
                    "id": ess.id,
                    "name": ess.name,
                    "code": ess.code,
                })
            resp_data.append(es_info)
        return self.report.post(resp_data)

    @request_url(EquipmentSubSystemCreateViewSchema)
    def eq_sub_sys_create(self, form_data):
        old_record = EquipmentSubSystem.query.filter_by(equipment_system_id=form_data["eq_sys_id"],
                                                        is_delete=IsDelete.NORMAL, code=form_data["code"]).first()
        if old_record:
            return self.report.error("编码重复")
        new_record = EquipmentSubSystem()
        new_record.equipment_system_id = form_data["eq_sys_id"]
        new_record.name = form_data["name"]
        new_record.code = form_data["code"]
        new_record.introduction = form_data["introduction"]
        new_record.creator_id = g.uid
        new_record.creator_name = g.account
        db.session.add(new_record)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(EquipmentSubSystemUpdateViewSchema)
    def eq_sub_sys_update(self, form_data):
        old_record = EquipmentSubSystem.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not old_record:
            return self.report.error("更改记录不存在~")
        if old_record.is_sys_conf == YesOrNo.YES and old_record.name != form_data["name"]:
            return self.report.error("系统默认配置的不允许修改名称~")
        old_record.name = form_data["name"]
        old_record.code = form_data["code"]
        old_record.introduction = form_data["introduction"]
        db.session.add(old_record)
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(EquipmentSubSystemSwitchViewSchema)
    def eq_sub_sys_active(self, form_data):
        status, msg = self.eq_sub_sys_switch(form_data, IsActive.Active)
        if status:
            return self.report.suc(msg)
        else:
            return self.report.error(msg)

    @request_url(EquipmentSubSystemSwitchViewSchema)
    def eq_sub_sys_disable(self, form_data):
        status, msg = self.eq_sub_sys_switch(form_data, IsActive.Disable)
        if status:
            return self.report.suc(msg)
        else:
            return self.report.error(msg)

    def eq_sub_sys_switch(self, form_data, status):
        record = EquipmentSubSystem.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if status == YesOrNo.NO and record.is_sys_conf == YesOrNo.YES:
            return False, "系统默认配置不允许停用"

        else:
            try:
                record.is_active = status
                db.session.add(record)
                if status == YesOrNo.NO:
                    EquipmentType.query.filter(EquipmentType.is_delete == IsDelete.NORMAL,
                                               EquipmentType.equipment_sub_system_id == record.id).update(
                        {"is_active": IsActive.Disable})
                else:
                    EquipmentType.query.filter(EquipmentType.is_delete == IsDelete.NORMAL,
                                               EquipmentType.equipment_sub_system_id == record.id).update(
                        {"is_active": IsActive.Active})
            except Exception as e:
                db.session.rollback()
                return False, str(e)
            db.session.commit()
            return True, "操作成功"

    @request_url(EquipmentTypeListViewSchema)
    def eq_type_list(self, form_data):
        eq_type_set = EquipmentType.query.filter_by(equipment_sub_system_id=form_data["eq_sub_sys_id"]).all()
        resp_data = []
        for eq_type in eq_type_set:
            resp_data.append({
                "id": eq_type.id,
                "name": eq_type.name,
                "code": eq_type.code,
                "introduction": eq_type.introduction,
                "is_sys_conf": eq_type.is_sys_conf,
                "extra_field": eq_type.extra_field,
                "is_active": eq_type.is_active,
            })
        return self.report.post(resp_data)

    @request_url(EquipmentTypeListViewSchema)
    def eq_type_list_simple(self, form_data):
        eq_type_set = EquipmentType.query.filter_by(equipment_sub_system_id=form_data["eq_sub_sys_id"],
                                                    is_active=YesOrNo.YES).all()
        resp_data = []
        for eq_type in eq_type_set:
            resp_data.append({
                "id": eq_type.id,
                "name": eq_type.name,
                "extra_field": eq_type.extra_field
            })
        return self.report.post(resp_data)

    @request_url(EquipmentCreateViewSchema)
    def eq_type_create(self, form_data):
        old_rd_name = EquipmentType.query.filter_by(name=form_data["name"],
                                                    equipment_sub_system_id=form_data[
                                                        "eq_sub_sys_id"]).first()
        if old_rd_name:
            return self.report.error("分类名重复~")
        old_rd_code = EquipmentType.query.filter_by(name=form_data["code"],
                                                    equipment_sub_system_id=form_data[
                                                        "eq_sub_sys_id"]).first()
        if old_rd_code:
            return self.report.error("分类编码重复~")

        # 处理额外字段的名称
        for item in form_data["extra_field"]:
            item["field_name"] = item["field_name"].strip().replace("）", ")").replace('（', "(")
        eq_type = EquipmentType()
        eq_type.name = form_data["name"]
        eq_type.code = form_data["code"]
        eq_type.introduction = form_data["introduction"]
        eq_type.extra_field = form_data["extra_field"]
        eq_type.equipment_sub_system_id = form_data["eq_sub_sys_id"]
        eq_type.creator_id = g.uid
        eq_type.creator_name = g.account
        db.session.add(eq_type)
        db.session.commit()
        return self.report.suc("添加成功")

    @request_url(EquipmentUpdateViewSchema)
    def eq_type_update(self, form_data):
        eq_type = EquipmentType.query.filter_by(id=form_data["id"]).first()
        if not eq_type:
            return self.report.error("相关记录不存在")
        if eq_type.name != form_data["name"]:
            old_rd_name = EquipmentType.query.filter_by(name=form_data["name"],
                                                        equipment_sub_system_id=eq_type.equipment_sub_system_id).first()
            if old_rd_name:
                return self.report.error("分类名重复~")
        if eq_type.code != form_data["code"]:
            old_rd_code = EquipmentType.query.filter_by(name=form_data["code"],
                                                        equipment_sub_system_id=eq_type.equipment_sub_system_id).first()
            if old_rd_code:
                return self.report.error("分类编码重复~")
        # 处理额外字段的名称
        for item in form_data["extra_field"]:
            item["field_name"] = item["field_name"].strip().replace("）", ")").replace('（', "(")
        eq_type.name = form_data["name"]
        eq_type.code = form_data["code"]
        eq_type.introduction = form_data["introduction"]
        eq_type.extra_field = form_data["extra_field"]
        db.session.add(eq_type)
        db.session.commit()
        return self.report.suc("更新成功")

    def switch_eq_type_status(self, form_data, status):
        eq_type = EquipmentType.query.filter_by(id=form_data["id"]).first()
        if not eq_type:
            return False, "相关记录不存在"
        if status == IsActive.Disable and eq_type.is_sys_conf == YesOrNo.YES:
            return False, "系统默认配置不允许停用"

        else:

            if status == IsActive.Active and eq_type.equipment_sub_system.is_active == YesOrNo.NO:
                return False, "父类未激活，禁止激活子类"
            eq_type.is_active = status
            db.session.add(eq_type)
            db.session.commit()
            return True, "操作成功"

    @request_url(EquipmentTypeSwitchViewSchema)
    def eq_type_active(self, form_data):
        status, msg = self.switch_eq_type_status(form_data, YesOrNo.YES)
        if status:
            return self.report.suc(msg)
        else:
            return self.report.error(msg)

    @request_url(EquipmentTypeSwitchViewSchema)
    def eq_type_disable(self, form_data):
        status, msg = self.switch_eq_type_status(form_data, YesOrNo.NO)
        if status:
            return self.report.suc(msg)
        else:
            return self.report.error(msg)


eq_sys_module = EquipmentSysTem()
