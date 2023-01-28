import re

from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.equipment.schema import *
from model_to_view.equipment_group.schema import *
from models import IsDelete, db, YesOrNo, IsActive, EquipmentStatus
from models.equipment import Equipment


class EquipmentGroupModule(ModuleBasic):
    """设备组"""

    @request_url(EquipmentGroupListSchema)
    def eq_group_list(self, form_data):
        filter_cond = [Equipment.status == EquipmentStatus.Using]
        if form_data.get("eq_id"):
            id_str = form_data["eq_id"][1:]
            try:
                if len(id_str) != 8 or not form_data["eq_id"].startswith("D"):
                    return self.report.table([], 0)
                id = int(id_str)
            except Exception as e:
                return self.report.table([], 0)
            filter_cond.append(Equipment.id == id)
        if form_data.get("equipment_type_id"):
            filter_cond.append(Equipment.equipment_type_id == form_data['equipment_type_id'])
        if form_data.get("code"):
            filter_cond.append(Equipment.code == form_data["code"])
        if form_data.get("name"):
            filter_cond.append(Equipment.name.like(f"%{form_data['name']}%"))
        if form_data.get("code"):
            filter_cond.append(Equipment.code == form_data["code"])

        eq_set = Equipment.query.filter(*filter_cond).order_by(Equipment.id.desc()).paginate(form_data["page"],
                                                                                             form_data["size"])
        resp_data = []
        for item in eq_set.items:
            resp_data.append({
                "id": item.id,
                "name": item.name,
                "code": item.code,
                "equipment_model": item.equipment_model,
                "eq_id": "D" + "%08d" % item.id,
                "location": f"{item.data_center.name}/{item.data_center_building.name}/{item.data_center_floor.name}/"
                            + f"{item.data_center_room.name}"
            })
        return self.report.table(resp_data, eq_set.total)


eq_group_module = EquipmentGroupModule()
