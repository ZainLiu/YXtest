import datetime

from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.eq_mt_item.schema import *
from model_to_view.eq_mt_item.serializer import EMIListSerializer, EMIDetailSerializer
from models import FlowStatus, db, MaintenanceItemStatus, FlowOpType, IsActive
from models.equipment import EquipmentSubSystem, EquipmentType
from models.maintenance_item import EquipmentMaintenanceItem
from models.maintenance_plan_timetable import EquipmentMtPlanTimetable, EquipmentMtPlanTimetableDetail
from module.eq_mt_item.flow_service import FlowServiceEMI
from utils.check_model_field import judge_data_has_finish_fill
from utils.flow_decorator import flow_decorator
from utils.injection_data import set_creator_and_belong_user_info
from utils.rpc_func import get_user_current_data_center_id
from utils.serial_number_service import get_serial_number_with_dc_code
from utils.time_util import TimeUtil
from utils.version_no import get_version_no


class EquipmentMaintenanceItemModule(ModuleBasic):

    def eq_mi_save_or_create(self, data, dc_id):
        if data.get("id"):
            mi = EquipmentMaintenanceItem.query.filter_by(id=data["id"]).first()
            if not mi:
                return self.report.error("相关数据不存在")
            mi.equipment_model = data.get("equipment_model", "")
            mi.equipment_type_id = data.get("equipment_type_id", None)
        else:
            mi = EquipmentMaintenanceItem()
            mi.data_center_id = dc_id
            # mi.flow_status = FlowStatus.Draft
            set_creator_and_belong_user_info(mi)
            mi.equipment_model = data.get("equipment_model", "")
            mi.equipment_type_id = data.get("equipment_type_id", None)
            if data.get("serial_number"):
                old_using_mi = EquipmentMaintenanceItem.query.filter_by(serial_number=data["serial_number"]).first()
                # 如果是更新版本则以下项不能修改
                mi.version_no = get_version_no(EquipmentMaintenanceItem, data["serial_number"])
                mi.serial_number = data["serial_number"]
                mi.equipment_model = old_using_mi.equipment_model
                mi.equipment_type_id = old_using_mi.equipment_type_id
            else:
                mi.serial_number = get_serial_number_with_dc_code(EquipmentMaintenanceItem, "WBMBM", dc_id)
                mi.version_no = 1
        mi.title = data.get("title", "")
        mi.mt_type = data.get("mt_type", None)
        mi.supporting_file = data.get("supporting_file", [])
        mi.qa_requirement = data.get("qa_requirement", "")
        mi.supplier_id = data.get("supplier_id", None)
        mi.monthly_template = data.get("monthly_template", None)
        mi.quarterly_template = data.get("quarterly_template", None)
        mi.semiannually_template = data.get("semiannually_template", None)
        mi.annually_template = data.get("annually_template", None)
        mi.manufacturer_id = data.get("manufacturer_id", None)
        mi.end_date = TimeUtil.get_date_from_datetime_str(data.get("end_date")) if data.get("end_date") else None
        db.session.add(mi)
        db.session.commit()
        return mi.id

    @request_url(EMISaveDraftSchema)
    def eq_mi_save_draft(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        draft_info = form_data["draft_info"]
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        self.eq_mi_save_or_create(draft_info, dc_id)

        return self.report.suc("模板保存成功")

    @request_url(EMISubmitSchema)
    @flow_decorator(FlowServiceEMI)
    def eq_mi_submit(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        fid = self.eq_mi_save_or_create(form_data, dc_id)
        g.fid = fid
        return self.report.suc("保存成功")

    @request_url(EMIListSchema)
    def eq_mi_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentMaintenanceItem.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentMaintenanceItem.serial_number == form_data["serial_number"])
        if form_data.get("title"):
            filter_cond.append(EquipmentMaintenanceItem.title.like(f'%{form_data["title"]}%'))
        if form_data.get("eq_type_id"):
            filter_cond.append(EquipmentMaintenanceItem.equipment_type_id == form_data["eq_type_id"])
        if form_data.get("eq_model"):
            filter_cond.append(EquipmentMaintenanceItem.equipment_model == form_data["eq_model"])

        mi_set = EquipmentMaintenanceItem.query.filter(*filter_cond).order_by(
            EquipmentMaintenanceItem.id.desc()).paginate(
            form_data["page"], form_data["size"])
        data = EMIListSerializer(many=True).dump(mi_set.items)
        return self.report.table(data, mi_set.total)

    @request_url(EMIListSimpleSchema)
    def eq_mi_list_simple(self, form_data):
        eq_sub_sys_set = EquipmentSubSystem.query.filter_by(equipment_system_id=form_data["eq_sys_id"]).all()
        eq_type_set = EquipmentType.query.filter(
            EquipmentType.equipment_sub_system_id.in_([eq_sub_sys.id for eq_sub_sys in eq_sub_sys_set])).all()

        empt_set = EquipmentMtPlanTimetable.query.filter_by(year=form_data["year"]).all()
        emptd_set = EquipmentMtPlanTimetableDetail.query.filter(
            EquipmentMtPlanTimetableDetail.empt_id.in_([empt.id for empt in empt_set])).all()

        emi_set = EquipmentMaintenanceItem.query.filter(
            EquipmentMaintenanceItem.equipment_type_id.in_([eq_type.id for eq_type in eq_type_set]),
            EquipmentMaintenanceItem.id.notin_([emptd.emi_id for emptd in emptd_set]),
            EquipmentMaintenanceItem.status == IsActive.Active).all()

        resp_data = []
        for emi in emi_set:
            if emi.mt_type == MaintenanceType.CustomMT and emi.end_date < datetime.date.today():
                continue
            resp_data.append({
                "id": emi.id,
                "eq_sys_name": emi.equipment_type.equipment_sub_system.equipment_system.name,
                "mt_serial_number": emi.serial_number,
                "monthly": 1 if emi.monthly_template else 0,
                "quarterly": 1 if emi.quarterly_template else 0,
                "semiannually": 1 if emi.semiannually_template else 0,
                "annually": 1 if emi.annually_template else 0,
                "mt_type": emi.mt_type,
                "end_date": TimeUtil.get_date_str_from_date(emi.end_date) if emi.end_date else None
            })

        return self.report.post(resp_data)

    @request_url(EMISwitchVersionSimpleSchema)
    def eq_mi_switch_version(self, form_data):
        emi = EquipmentMaintenanceItem.query.filter_by(id=form_data["id"]).first()
        if not emi:
            return self.report.error("相关数据不存在")
        if emi.flow_status != FlowStatus.Done:
            return self.report.error("审批未通过的版本禁止切换")
        try:
            emi.status = IsActive.Active
            db.session.add(emi)
            EquipmentMaintenanceItem.query.filter(EquipmentMaintenanceItem.id != emi.id,
                                                  EquipmentMaintenanceItem.serial_number == emi.serial_number,
                                                  EquipmentMaintenanceItem.status == IsActive.Active).update(
                {"status": IsActive.Disable})
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"版本切换失败，原因：{str(e)}")
        db.session.commit()
        return self.report.suc("切换成功")

    @request_url(EMIDetailSchema)
    def eq_mi_detail(self, form_data):
        emi = EquipmentMaintenanceItem.query.filter_by(id=form_data["id"]).first()
        if not emi:
            return self.report.error("相关数据不存在")
        resp_data = EMIDetailSerializer().dump(emi)
        return self.report.post(resp_data)

    @request_url(EMIDetailSchema)
    @flow_decorator(FlowServiceEMI)
    def eq_mi_approval(self, form_data):
        emi = EquipmentMaintenanceItem.query.filter_by(id=form_data["id"]).first()
        if not emi:
            return self.report.error("相关数据不存在")
        if emi.flow_status not in FlowStatus.CAN_APPROVAL:
            return self.report.error("该表单不能发起审批")
        res, field = judge_data_has_finish_fill(emi, ["title", "equipment_model", "equipment_type_id"])
        if not res:
            return self.report.error(f"{field}必填")
        if emi.mt_type == MaintenanceType.SupplierMT and not emi.supplier_id:
            return self.report.error("供应商维保，供应商必填")
        g.fid = emi.id
        return self.report.suc("发起成功")


eq_mi_module = EquipmentMaintenanceItemModule()
