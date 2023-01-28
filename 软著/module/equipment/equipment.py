import re

from flask import g, request
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.equipment.schema import *
from models import db, EquipmentStatus, IsDelete, ExtraFieldType, IsActive, YesOrNo
from models.data_center import DataCenter, DataCenterBuilding, DataCenterFloor, DataCenterRoom, RoomType
from models.dictionary import Dictionary
from models.equipment import Equipment, EquipmentSystem, EquipmentSubSystem, EquipmentType
from models.manufacturer import Manufacturer
from utils.code_util import CodeUtil
import pandas as pd

from utils.rpc_func import get_user_current_data_center_id


class EquipmentModule(ModuleBasic):

    @request_url(EquipmentCreateSchema)
    def eq_create(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        old_record = Equipment.query.filter_by(name=form_data["code"],
                                               equipment_type_id=form_data["equipment_type_id"]).first()
        if old_record:
            return self.report.error("编码重复~")
        if form_data["status"] == EquipmentStatus.Using:
            old_record = Equipment.query.filter_by(name=form_data["name"], status=EquipmentStatus.Using,
                                                   equipment_type_id=form_data["equipment_type_id"]).first()
            if old_record:
                return self.report.error("已有使用中的同名设备，禁止添加~")
        eq = Equipment()
        eq.name = form_data["name"]
        eq.code = form_data["code"]
        eq.sn_code = form_data["sn_code"]
        eq.data_center_id = data_center_id
        eq.data_center_building_id = form_data["data_center_building_id"]
        eq.data_center_floor_id = form_data["data_center_floor_id"]
        eq.data_center_room_id = form_data["data_center_room_id"]
        eq.equipment_model = form_data["equipment_model"]
        # eq.has_identification = form_data["has_identification"]
        eq.produce_time = form_data["produce_time"]
        eq.introduction = form_data["introduction"]
        eq.extra_field = form_data["extra_field"]
        eq.manufacturer_id = form_data["manufacturer_id"]
        eq.equipment_type_id = form_data["equipment_type_id"]
        eq.status = form_data["status"]
        eq.creator_id = g.uid
        eq.creator_name = g.account
        db.session.add(eq)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(EquipmentUpdateSchema)
    def eq_update(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        eq = Equipment.query.filter_by(id=form_data["id"]).first()
        if eq.code != form_data["code"]:
            old_record = Equipment.query.filter_by(name=form_data["code"],
                                                   equipment_type_id=eq.equipment_type_id).first()
            if old_record:
                return self.report.error("编码重复~")
        if form_data["status"] != eq.status and form_data["status"] == EquipmentStatus.Using:
            old_record = Equipment.query.filter_by(name=form_data["name"], status=EquipmentStatus.Using,
                                                   equipment_type_id=eq.equipment_type_id).first()
            if old_record:
                return self.report.error("已有使用中的同名设备，禁止变更为使用中~")
        eq.name = form_data["name"]
        eq.code = form_data["code"]
        eq.sn_code = form_data["sn_code"]
        eq.data_center_id = data_center_id
        eq.data_center_building_id = form_data["data_center_building_id"]
        eq.data_center_floor_id = form_data["data_center_floor_id"]
        eq.data_center_room_id = form_data["data_center_room_id"]
        eq.equipment_model = form_data["equipment_model"]
        # eq.has_identification = form_data["has_identification"]
        eq.produce_time = form_data["produce_time"]
        eq.introduction = form_data["introduction"]
        eq.extra_field = form_data["extra_field"]
        eq.manufacturer_id = form_data["manufacturer_id"]
        eq.equipment_type_id = form_data["equipment_type_id"]
        eq.status = form_data["status"]
        db.session.add(eq)
        db.session.commit()
        return self.report.suc("变更成功")

    @request_url(EquipmentListSchema)
    def eq_list(self, form_data):
        filter_cond = []
        if form_data.get("eq_id"):
            id_str = form_data["eq_id"][1:]
            try:
                if len(id_str) != 8 or form_data["eq_id"].startswith("D"):
                    return self.report.table([], 0)
                id = int(id_str)
            except Exception as e:
                return self.report.table([], 0)
            filter_cond.append(Equipment.id == id)
        if form_data.get("equipment_type_id"):
            filter_cond.append(Equipment.equipment_type_id == form_data['equipment_type_id'])
        if form_data.get("name"):
            filter_cond.append(Equipment.name.like(f"%{form_data['name']}%"))
        if form_data.get("code"):
            filter_cond.append(Equipment.code == form_data["code"])
        if form_data.get("status"):
            filter_cond.append(Equipment.status == form_data["status"])
        eq_set = Equipment.query.filter(*filter_cond).order_by(Equipment.id.desc()).paginate(form_data["page"],
                                                                                             form_data["size"])
        resp_data = []
        for item in eq_set.items:
            resp_data.append({
                "id": item.id,
                "name": item.name,
                "status": item.status,
                "code": item.code,
                "equipment_model": item.equipment_model,
                "eq_id": "D" + "%08d" % item.id,
                "full_code": CodeUtil.get_eq_full_code(item)
            })
        return self.report.table(resp_data, eq_set.total)

    @request_url(EquipmentDetailSchema)
    def eq_detail(self, form_data):
        eq = Equipment.query.filter_by(id=form_data["id"]).first()
        if not eq:
            return self.report.error("相关数据不存在")
        resp_data = {
            "id": eq.id,
            "name": eq.name,
            "status": eq.status,
            "code": eq.code,
            "equipment_model": eq.equipment_model,
            "eq_id": "D" + "%08d" % eq.id,
            "equipment_system_name": eq.equipment_type.equipment_sub_system.equipment_system.name,
            "equipment_sub_system_name": eq.equipment_type.equipment_sub_system.name,
            "equipment_type_name": eq.equipment_type.name,
            "equipment_type_id": eq.equipment_type.id,
            "data_center_id": eq.data_center.id,
            "data_center_name": eq.data_center.name,
            "data_center_building_id": eq.data_center_building.id,
            "data_center_building_name": eq.data_center_building.name,
            "data_center_floor_id": eq.data_center_floor.id,
            "data_center_floor_name": eq.data_center_floor.name,
            "data_center_room_id": eq.data_center_room.id,
            "data_center_room_name": eq.data_center_room.name,
            "full_code": CodeUtil.get_eq_full_code(eq),
            "extra_field": eq.extra_field,
            "manufacturer_id": eq.manufacturer_id,
            "manufacturer_name": eq.manufacturer.name,
            "manufacturer_contracts": eq.manufacturer.contacts,
            "sn_code": eq.sn_code,
            # "has_identification": eq.has_identification,
            "introduction": eq.introduction,
            "produce_time": eq.produce_time.strftime(current_app.config['APP_DATE_FORMAT']),
            "location": CodeUtil.get_eq_location(eq),
            "type": CodeUtil.get_eq_type(eq)
        }
        return self.report.post(resp_data)

    def get_eq_extra_field_info(self, data_center_id):
        eq_type_set = EquipmentType.query.filter_by(is_delete=IsDelete.NORMAL).all()
        eq_extra_field_info = {}
        for eq_type in eq_type_set:
            data = {}
            for field in eq_type.extra_field:
                try:
                    data[field["field_name"]] = {
                        "field_type": field["field_type"],
                        "is_required": field["is_required"]
                    }
                except Exception as e:
                    print(field)
                    pass
            eq_extra_field_info[eq_type.id] = data
        return eq_extra_field_info

    @request_url(EquipmentUploadSchema)
    def upload(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        file = request.files.get("file")
        df_total = pd.read_excel(file, sheet_name=None)
        # 校验数据
        company_dict = {}
        country_dict = {}
        province_dict = {}
        data_center_dict = {}
        dcb_dict = {}
        dcf_dict = {}
        dcr_dict = {}
        eq_sys_dict = {}
        eq_sub_sys_dict = {}
        eq_type_dict = {}
        mf_dict = {}
        eq_extra_field_info = self.get_eq_extra_field_info(data_center_id)
        room_type_set = RoomType.query.filter_by(is_delete=IsDelete.NORMAL, is_active=YesOrNo.YES).all()
        room_type_info = {}
        for room_type in room_type_set:
            room_type_info[room_type.code] = room_type.id
        # 处理设备类型
        for sheet_name, df in df_total.items():
            for index in df.index:
                row = df.loc[index]
                # row = row_raw.values
                # 校验公司名
                company_name = row["公司名称"]
                if not company_dict.get(company_name):
                    company = Dictionary.query.filter_by(name=company_name, is_delete=IsDelete.NORMAL).first()
                    if not company:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{company_name}》公司名填写错误或者尚未创建，请去字典模块检查")
                    else:
                        company_dict[company_name] = company.id
                # 校验国家名
                country_name = row["国家名称"]
                if not country_dict.get(country_name):
                    country = Dictionary.query.filter_by(name=company_name, is_delete=IsDelete.NORMAL).first()
                    if not country:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{country_name}》国家名填写错误或者尚未创建，请去字典模块检查")
                    else:
                        country_dict[country_name] = country.id
                # 校验省份名
                province_name = row["省份名称"]
                if not province_dict.get(province_name):
                    province = Dictionary.query.filter_by(name=province_name, is_delete=IsDelete.NORMAL).first()
                    if not province:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{province_name}》省份名填写错误或者尚未创建，请去字典模块检查")
                    else:
                        province_dict[province_name] = province.id
                # 校验园区名
                data_center_name = row["园区名称"]
                if not data_center_dict.get(data_center_name):
                    data_center = DataCenter.query.filter_by(name=data_center_name, is_delete=IsDelete.NORMAL).first()
                    if not data_center:
                        return self.report.error(
                            f"{sheet_name}第{index + 2}行《{data_center_name}》数据中心名填写错误或者尚未创建，请去数据中心模块检查")
                    else:
                        data_center_dict[data_center_name] = data_center.id
                # 校验楼栋名
                dcb_name = row["栋数名称"]
                if not dcb_dict.get(f"{data_center_name}-{dcb_name}"):
                    dcb = DataCenterBuilding.query.filter_by(name=dcb_name,
                                                             data_center_id=data_center_dict[data_center_name],
                                                             is_delete=IsDelete.NORMAL).first()
                    if not dcb:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{dcb_name}》数据中心楼栋名填写错误或者尚未创建，请去数据中心模块检查")
                    else:
                        dcb_dict[f"{data_center_name}-{dcb_name}"] = dcb.id
                # 校验楼层名
                dcf_name = row["楼层"]
                if not dcf_dict.get(f"{data_center_name}-{dcb_name}-{dcf_name}"):
                    dcf = DataCenterFloor.query.filter_by(name=dcf_name,
                                                          data_center_building_id=dcb_dict[
                                                              f"{data_center_name}-{dcb_name}"],
                                                          is_delete=IsDelete.NORMAL).first()
                    if not dcf:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{dcf_name}》数据中心楼层名填写错误或者尚未创建，请去数据中心模块检查")
                    else:
                        dcf_dict[f"{data_center_name}-{dcb_name}-{dcf_name}"] = dcf.id
                # 校验房间名
                dcr_name = row["房间编号"]
                if not dcr_dict.get(f"{data_center_name}-{dcb_name}-{dcf_name}-{dcr_name}"):
                    # if not row["楼层"].startswith("负"):
                    #     result = re.match(r"(.+?)(\d+)", dcr_name)
                    # else:
                    #     result = re.match(r"(.+?)B(\d+)", dcr_name)
                    try:
                        dcr = DataCenterRoom.query.filter(DataCenterRoom.code == dcr_name[-4:],
                                                          DataCenterRoom.data_center_floor_id == dcf_dict[
                                                              f"{data_center_name}-{dcb_name}-{dcf_name}"],
                                                          DataCenterRoom.room_type_id == room_type_info[dcr_name[:-4]],
                                                          DataCenterRoom.is_delete == IsDelete.NORMAL).first()
                    except Exception as e:
                        print(dcr_name)
                        print(f"{sheet_name}第{index + 2}行")
                        raise e
                    if not dcr:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{dcr_name}》数据中心房间名填写错误或者尚未创建，请去数据中心模块检查")
                    else:
                        dcr_dict[f"{data_center_name}-{dcb_name}-{dcf_name}-{dcr_name}"] = dcr.id
                # 校验所属系统
                eq_sys_name = row["所属系统"]
                if not eq_sys_dict.get(f"{data_center_name}-{eq_sys_name}"):
                    eq_sys = EquipmentSystem.query.filter_by(name=eq_sys_name,
                                                             data_center_id=data_center_dict[data_center_name]).first()
                    if not eq_sys:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{eq_sys_name}》所属系统名填写错误或者尚未创建，请检查无误后再提交")
                    else:
                        eq_sys_dict[f"{data_center_name}-{eq_sys_name}"] = eq_sys.id
                # 校验所属子系统
                eq_sub_sys_name = row["所属子系统"]
                if not eq_sub_sys_dict.get(f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}"):
                    eq_sub_sys = EquipmentSubSystem.query.filter_by(name=eq_sub_sys_name,
                                                                    equipment_system_id=eq_sys_dict[
                                                                        f"{data_center_name}-{eq_sys_name}"],
                                                                    is_delete=IsDelete.NORMAL).first()
                    if not eq_sub_sys:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{eq_sys_name}》所属子系统名填写错误或者尚未创建，请检查无误后再提交")
                    else:
                        eq_sub_sys_dict[f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}"] = eq_sub_sys.id
                # 校验设备类型
                eq_type_name = row["设备类型名称"]
                if not eq_type_dict.get(f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}-{eq_type_name}"):
                    eq_type = EquipmentType.query.filter_by(name=eq_type_name,
                                                            equipment_sub_system_id=eq_sub_sys_dict[
                                                                f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}"],
                                                            is_delete=IsDelete.NORMAL).first()
                    if not eq_type:
                        print(f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}-{eq_type_name}")
                        return self.report.error(
                            f"{sheet_name}第{index + 2}行《{eq_type_name}》所属设备类型名填写错误或者尚未创建，请检查无误后再提交")
                    else:
                        eq_type_dict[f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}-{eq_type_name}"] = eq_type.id
                # 校验厂商
                mf_name = row["厂商"]
                if not mf_dict.get(mf_name):
                    mf = Manufacturer.query.filter_by(name=mf_name, is_delete=IsDelete.NORMAL).first()
                    if not eq_type:
                        return self.report.error(f"{sheet_name}第{index + 2}行《{mf_name}》厂商名填写错误或者尚未创建，请检查无误后再提交")
                    else:
                        print(mf_name)
                        mf_dict[mf_name] = mf.id
                # 校验额外字段是否合法
                extra_field_info = eq_extra_field_info[
                    eq_type_dict[f"{data_center_name}-{eq_sys_name}-{eq_sub_sys_name}-{eq_type_name}"]]
                for key, val in extra_field_info.items():
                    # 去掉左右空格
                    key = key.strip()
                    if key not in df.keys():
                        return self.report.error(f"{sheet_name}第{index + 2}行缺少一个额外字段信息，该字段为:{key}")
                    else:
                        value = row.get(key)
                        if pd.isnull(value) and val["is_required"] == 1:
                            return self.report.error(f"{sheet_name}第{index + 2}行缺少一个额外字段的值，此值为必传，该字段为:{key}")
                        if val["field_type"] == ExtraFieldType.Number:
                            try:
                                temp_val = float(value)
                            except Exception as e:
                                return self.report.error(f"{sheet_name}第{index + 2}行额外字段{key}的值必须为数字，现在的值为{value}")

        # 新增设备
        for sheet_name, df in df_total.items():
            for index in df.index:
                row = df.loc[index]
                # 校验是否已经有同名且在使用中的设备
                old_record = Equipment.query.filter_by(name=row["设备名称"], status=EquipmentStatus.Using,
                                                       data_center_id=data_center_dict[row["园区名称"]],
                                                       equipment_type_id=eq_type_dict[
                                                           f'{row["园区名称"]}-{row["所属系统"]}-{row["所属子系统"]}-{row["设备类型名称"]}']).first()
                # 已有同名且存在使用中的设备则跳过不新增
                if old_record:
                    continue
                eq = Equipment()
                eq.name = row["设备名称"]
                eq.code = row["设备编号"]
                eq.sn_code = row["型号"]
                eq.data_center_id = data_center_dict[row["园区名称"]]
                eq.data_center_building_id = dcb_dict[f"{row['园区名称']}-{row['栋数名称']}"]
                eq.data_center_floor_id = dcf_dict[f'{row["园区名称"]}-{row["栋数名称"]}-{row["楼层"]}']
                eq.data_center_room_id = dcr_dict[f'{row["园区名称"]}-{row["栋数名称"]}-{row["楼层"]}-{row["房间编号"]}']
                eq.equipment_model = row["型号"]
                # eq.has_identification = int(row["有无标识"])
                eq.produce_time = row["投产日期"]
                eq.manufacturer_id = mf_dict[row["厂商"]]
                eq.equipment_type_id = eq_type_dict[f'{row["园区名称"]}-{row["所属系统"]}-{row["所属子系统"]}-{row["设备类型名称"]}']
                eq.status = EquipmentStatus.Using
                eq.creator_id = g.uid
                eq.creator_name = g.account
                extra_field_info = eq_extra_field_info[
                    eq_type_dict[f'{row["园区名称"]}-{row["所属系统"]}-{row["所属子系统"]}-{row["设备类型名称"]}']]
                extra_field = []
                for key, val in extra_field_info.items():
                    key = key.strip()
                    if val["is_required"] == 0 and pd.isnull(row[key]):
                        value = None
                    elif val["field_type"] == ExtraFieldType.Number and not pd.isnull(row[key]):
                        value = float(row[key])
                    else:
                        value = str(row[key])
                    extra_field.append({
                        "field_name": key,
                        "field_type": val["field_type"],
                        "is_required": val["is_required"],
                        "value": value
                    })
                eq.extra_field = extra_field
                db.session.add(eq)

        db.session.commit()
        return self.report.suc("上传成功")


eq_module = EquipmentModule()
