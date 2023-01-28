from flask import g
from ly_kernel.Module import ModuleBasic, request_url
from sqlalchemy.orm import joinedload

from model_to_view.cabinet_management.schema import *
from model_to_view.equipment_group.schema import *
from models import IsDelete, db, EquipmentStatus
from models.data_center import CabinetColumn
from models.equipment import Equipment, EquipmentType, CabRoomColumnRelationship
from utils.code_util import CodeUtil


class CabinetManagementModule(ModuleBasic):

    @request_url(CabinetManagementBaseSchema)
    def create_cabinet_column(self, form_data):
        last_cab_col = CabinetColumn.query.filter_by(data_center_room_id=form_data["data_center_room_id"],
                                                     is_delete=IsDelete.NORMAL).order_by(
            CabinetColumn.no.desc()).first()
        if not last_cab_col:
            no = 1
        else:
            no = last_cab_col.no + 1

        new_cab_col = CabinetColumn()
        new_cab_col.no = no
        new_cab_col.data_center_room_id = form_data["data_center_room_id"]
        new_cab_col.creator_id = g.uid
        new_cab_col.creator_name = g.account
        db.session.add(new_cab_col)
        db.session.commit()
        return self.report.post({"id": new_cab_col.id, "no": new_cab_col.no})

    @request_url(CabinetManagementBaseSchema)
    def list_cab_col(self, form_data):
        cab_col_set = CabinetColumn.query.filter_by(data_center_room_id=form_data["data_center_room_id"],
                                                    is_delete=IsDelete.NORMAL).all()
        resp_data = []
        for cab_col in cab_col_set:
            resp_data.append({
                "id": cab_col.id,
                "no": cab_col.no
            })
        return self.report.post(resp_data)

    @request_url(CabinetManagementCabListSchema)
    def list_cab(self, form_data):

        crcr_set = CabRoomColumnRelationship.query.join(Equipment).filter(
            Equipment.data_center_room_id == form_data["data_center_room_id"],
            CabRoomColumnRelationship.is_delete == IsDelete.NORMAL).all()
        has_bind_eq_id_list = [crcr.equipment_id for crcr in crcr_set]
        filter_cond = [
            Equipment.data_center_room_id == form_data["data_center_room_id"],
            Equipment.is_delete == IsDelete.NORMAL, EquipmentType.code == "R",
            Equipment.status == EquipmentStatus.Using, Equipment.id.notin_(has_bind_eq_id_list)
        ]
        if form_data.get("name"):
            filter_cond.append(Equipment.name.like(f'%{form_data["name"]}%'))
        cab_set = Equipment.query.join(EquipmentType).options(joinedload(Equipment.data_center),
                                                              joinedload(Equipment.data_center_building),
                                                              joinedload(Equipment.data_center_floor),
                                                              joinedload(Equipment.data_center_room),
                                                              joinedload(Equipment.manufacturer)).filter(
            *filter_cond).order_by(
            Equipment.id.desc()).paginate(form_data["page"], form_data["size"])
        resp_data = []
        for item in cab_set.items:
            resp_data.append({
                "id": item.id,
                "name": item.name,
                "full_code": CodeUtil.get_eq_full_code(item),
                "sys": item.equipment_type.equipment_sub_system.name
            })
        return self.report.table(resp_data, cab_set.total)

    @request_url(CabinetManagementCabAddSchema)
    def bind_cab_with_cab_column(self, form_data):
        # 加锁更新
        flag = LieYingApp.redis.get("bind_cab_with_cab_column")
        if flag:
            return self.report.error("操作频繁")
        else:
            LieYingApp.redis.setex("bind_cab_with_cab_column", 3, 1)
        cab_col = CabinetColumn.query.filter_by(id=form_data["column_id"]).first()
        if not cab_col:
            return self.report.error("机柜列不存在")
        location_list = []
        for item in form_data["cab_list"]:
            if not item.get("location"):
                return self.report.error("请填写完整机柜位置再保存")
            if not item["location"].isdigit():
                return self.report.error("机柜位置请填写数字")
            location_list.append(item["location"])
        if len(set(location_list)) != len(form_data["cab_list"]):
            return self.report.error("机柜位置有重复，请确认无误后再提交")
        try:
            for item in form_data["cab_list"]:
                if not item.get("r_id"):
                    ccr = CabRoomColumnRelationship(
                        equipment_id=item.get("equipment_id"),
                        location=item.get("location"),
                        column_id=form_data["column_id"],
                        creator_id=g.uid,
                        creator_name=g.account,
                    )
                else:
                    ccr = CabRoomColumnRelationship.query.get(item.get("r_id"))
                    ccr.location = item["location"]
                db.session.add(ccr)
        except Exception as e:
            db.session.rollback()
            raise e
        db.session.commit()
        return self.report.suc("保存成功")

    @request_url(CabinetManagementCabListByColumnSchema)
    def cab_list_by_col(self, form_data):
        filter_cond = [
            CabRoomColumnRelationship.column_id == form_data["column_id"],
            CabRoomColumnRelationship.is_delete == IsDelete.NORMAL
        ]
        if form_data.get("name"):
            filter_cond.append(Equipment.name.like(f'%{form_data["name"]}%'))
        crcr_set = CabRoomColumnRelationship.query.join(Equipment).options(joinedload(CabRoomColumnRelationship.equipment)).filter(
            *filter_cond).all()
        resp_data = []
        for crcr in crcr_set:
            resp_data.append({
                "r_id": crcr.id,
                "eq_id": crcr.equipment_id,
                "location": crcr.location,
                "eq_name": crcr.equipment.name,
                "full_code": CodeUtil.get_eq_full_code(crcr.equipment),
                "res_no": CodeUtil.get_cab_res_no(crcr)
            })
        return self.report.post(resp_data)

    @request_url(CabinetManagementDeleteCRCRSchema)
    def delete_crcr(self, form_data):
        crcr = CabRoomColumnRelationship.query.filter_by(id=form_data["r_id"]).first()
        if crcr:
            crcr.is_delete = IsDelete.Deleted
            db.session.add(crcr)
            db.session.commit()
        return self.report.suc("删除成功")


cab_mgm_module = CabinetManagementModule()
