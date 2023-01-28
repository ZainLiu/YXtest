import datetime

from flask import g
from ly_kernel.Module import ModuleBasic, request_url
from sqlalchemy.orm import joinedload

from models import FlowStatus, db, MaintenanceItemStatus, MaintenanceType, IsActive
from models.equipment import EquipmentSubSystem, Equipment, EquipmentType, EquipmentSystem
from models.maintenance_item import EquipmentMaintenanceItem, EquipmentSubSystemMaintenanceItem
from models.maintenance_plan_timetable import EquipmentSubSystemMtPlanTimetable, EquipmentSubSystemMtPlanTimetableDetail
from module.ess_mt_item.flow_service import FlowServiceESSMI
from module.ess_mt_item.serializers.schema import EssmiSaveDraftSchema, EssmiListEquipmentSchema, ESSMIListSchema, \
    ESSMIDetailSchema, ESSMISwitchVersionSchema, ESSMIListSimpleSchema
from module.ess_mt_item.serializers.serializer import ESSMIListSerializer, ESSMIDetailSerializer
from utils.check_model_field import judge_data_has_finish_fill
from utils.code_util import CodeUtil
from utils.flow_decorator import flow_decorator
from utils.injection_data import set_creator_and_belong_user_info
from utils.rpc_func import get_user_current_data_center_id
from utils.serial_number_service import get_serial_number_with_dc_code
from utils.time_util import TimeUtil
from utils.version_no import get_version_no


class EquipmentSubSystemMaintenanceItemModule(ModuleBasic):

    @request_url(EssmiSaveDraftSchema)
    def essmi_save_or_create(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        data = form_data["draft_info"]
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        draft_info = form_data["draft_info"]
        try:
            if draft_info.get("id"):
                mi = EquipmentSubSystemMaintenanceItem.query.filter_by(id=data["id"]).first()
                if not mi:
                    return self.report.error("相关数据不存在")
                mi.equipment_sub_system_id = data.get("equipment_sub_system_id", None)
            else:
                mi = EquipmentSubSystemMaintenanceItem()
                mi.data_center_id = dc_id
                # mi.flow_status = FlowStatus.Draft
                set_creator_and_belong_user_info(mi)
                mi.equipment_sub_system_id = data.get("equipment_sub_system_id", None)
                if data.get("serial_number"):
                    old_using_mi = EquipmentSubSystemMaintenanceItem.query.filter_by(
                        serial_number=data["serial_number"]).first()
                    # 如果是更新版本则以下项不能修改
                    mi.version_no = get_version_no(EquipmentSubSystemMaintenanceItem, data["serial_number"])
                    mi.serial_number = data["serial_number"]
                    mi.equipment_sub_system_id = old_using_mi.equipment_sub_system_id
                else:
                    mi.serial_number = get_serial_number_with_dc_code(EquipmentSubSystemMaintenanceItem, "WBMBS", dc_id)
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
            mi.batch_conf = data.get("batch_conf")
            db.session.add(mi)
            # 处理批次,改为审批后读取batch_conf去创建
        except Exception as e:
            db.session.rollback()
            return self.report.error("保存失败")
        db.session.commit()
        return self.report.suc("保存成功")

    @request_url(EssmiListEquipmentSchema)
    def get_eq_classification(self, form_data):

        eq_set = Equipment.query.join(EquipmentType, EquipmentSubSystem).options(
            joinedload(Equipment.data_center),
            joinedload(Equipment.data_center_building),
            joinedload(Equipment.data_center_floor),
            joinedload(Equipment.data_center_room), joinedload(Equipment.equipment_type)).filter(
            EquipmentSubSystem.id == form_data["id"]).all()
        eq_info_dict = dict()
        for eq in eq_set:
            dcb = eq.data_center_building
            building_info = eq_info_dict.get(dcb.id, {"name": dcb.name, "id": dcb.id, "floor_info": {}})
            dcf = eq.data_center_floor
            floor_info = building_info["floor_info"].get(dcf.id, {"name": dcf.name, "id": dcf.id, "room_info": {}})
            dcr = eq.data_center_room
            room_info = floor_info["room_info"].get(dcr.id, {"name": dcr.name, "id": dcr.id, "eq_info": []})
            room_info["eq_info"].append({
                "id": eq.id,
                "name": eq.name,
                "full_code": CodeUtil.get_eq_full_code(eq),
                "location": CodeUtil.get_eq_location(eq),
                "eq_type_name": eq.equipment_type.name
            })
            floor_info["room_info"][dcr.id] = room_info
            building_info["floor_info"][dcf.id] = floor_info
            eq_info_dict[dcb.id] = building_info
        # 处理成前端能看懂的数据格式
        eq_info = []
        for building_id, building_info in eq_info_dict.items():
            floors_info = []
            for floor_id, floor_info in building_info["floor_info"].items():
                rooms_info = []
                for _, room_info in floor_info["room_info"].items():
                    rooms_info.append(room_info)
                floor_info["room_info"] = rooms_info
                floors_info.append(floor_info)
            building_info["floor_info"] = floors_info
            eq_info.append(building_info)
        resp_data = eq_info
        return self.report.post(resp_data)

    @request_url(ESSMIListSchema)
    def essmi_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentSubSystemMaintenanceItem.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentSubSystemMaintenanceItem.serial_number == form_data["serial_number"])
        if form_data.get("title"):
            filter_cond.append(EquipmentSubSystemMaintenanceItem.title.like(f"%{form_data['title']}%"))
        if form_data.get("eq_sys_id"):
            filter_cond.append(EquipmentSystem.id == form_data["eq_sys_id"])
        mi_set = EquipmentSubSystemMaintenanceItem.query.join(EquipmentSubSystem, EquipmentSystem).filter(
            *filter_cond).order_by(
            EquipmentSubSystemMaintenanceItem.id.desc()).paginate(
            form_data["page"], form_data["size"])
        data = ESSMIListSerializer(many=True).dump(mi_set.items)
        return self.report.table(data, mi_set.total)

    @request_url(ESSMIDetailSchema)
    def essmi_detail(self, form_data):
        essmi = EquipmentSubSystemMaintenanceItem.query.filter_by(id=form_data["id"]).first()
        if not essmi:
            return self.report.error("相关数据不存在")
        resp_data = ESSMIDetailSerializer().dump(essmi)
        return self.report.post(resp_data)

    @request_url(ESSMISwitchVersionSchema)
    def essmi_switch_version(self, form_data):
        essmi = EquipmentSubSystemMaintenanceItem.query.filter_by(id=form_data["id"]).first()
        if not essmi:
            return self.report.error("相关数据不存在")
        if essmi.flow_status != FlowStatus.Done:
            return self.report.error("审批未通过的版本禁止切换")
        try:
            essmi.status = IsActive.Active
            db.session.add(essmi)
            EquipmentSubSystemMaintenanceItem.query.filter(EquipmentSubSystemMaintenanceItem.id != essmi.id,
                                                           EquipmentSubSystemMaintenanceItem.serial_number == essmi.serial_number,
                                                           EquipmentSubSystemMaintenanceItem.status == IsActive.Active).update(
                {"status": IsActive.Disable})
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"版本切换失败，原因：{str(e)}")
        db.session.commit()
        return self.report.suc("切换成功")

    @request_url(ESSMIDetailSchema)
    @flow_decorator(FlowServiceESSMI)
    def essmi_approval(self, form_data):
        essmi = EquipmentSubSystemMaintenanceItem.query.filter_by(id=form_data["id"]).first()
        if not essmi:
            return self.report.error("相关数据不存在")
        if essmi.flow_status not in FlowStatus.CAN_APPROVAL:
            return self.report.error("该表单不能发起审批")
        res, field = judge_data_has_finish_fill(essmi, ["title", "equipment_sub_system_id", "batch_conf"])
        if not res:
            return self.report.error(f"{field}必填")

        for batch in essmi.batch_conf:
            if not batch.get("eq_info"):
                return self.report.error("每个批次至少选择一个设备，否则不能提交")

        if essmi.mt_type == MaintenanceType.SupplierMT and not essmi.supplier_id:
            return self.report.error("供应商维保，供应商必填")
        g.fid = essmi.id
        return self.report.suc("发起成功")

    @request_url(ESSMIListSimpleSchema)
    def essmi_list_simple(self, form_data):
        eq_sub_sys_set = EquipmentSubSystem.query.filter_by(equipment_system_id=form_data["eq_sys_id"]).all()
        essmpt_set = EquipmentSubSystemMtPlanTimetable.query.filter_by(year=form_data["year"]).all()
        essmptd_set = EquipmentSubSystemMtPlanTimetableDetail.query.filter(
            EquipmentSubSystemMtPlanTimetableDetail.essmpt_id.in_([essmpt.id for essmpt in essmpt_set])).all()

        essmi_set = EquipmentSubSystemMaintenanceItem.query.filter(
            EquipmentSubSystemMaintenanceItem.equipment_sub_system_id.in_(
                [eq_sub_sys.id for eq_sub_sys in eq_sub_sys_set]),
            EquipmentSubSystemMaintenanceItem.id.notin_([essmptd.essmi_id for essmptd in essmptd_set]),
            EquipmentSubSystemMaintenanceItem.status == IsActive.Active).all()

        resp_data = []
        for essmi in essmi_set:
            if essmi.mt_type == MaintenanceType.CustomMT and essmi.end_date <=datetime.date.today():
                continue
            resp_data.append({
                "id": essmi.id,
                "eq_sys_name": essmi.equipment_sub_system.equipment_system.name,
                "mt_serial_number": essmi.serial_number,
                "monthly": 1 if essmi.monthly_template else 0,
                "quarterly": 1 if essmi.quarterly_template else 0,
                "semiannually": 1 if essmi.semiannually_template else 0,
                "annually": 1 if essmi.annually_template else 0,
                "mt_type": essmi.mt_type,
                "end_date": TimeUtil.get_date_str_from_date(essmi.end_date) if essmi.end_date else None
            })

        return self.report.post(resp_data)


essmi_module = EquipmentSubSystemMaintenanceItemModule()
