from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.data_center.schema import DataCenterAddFloorSchema, DataCenterFloorViewSchema, \
    DataCenterFloorSimpleViewSchema, DataCenterUpdateFloorSchema, DataCenterFloorViewFromBuildingIDSchema
from models import IsDelete, db
from models.data_center import DataCenterFloor, DataCenterBuilding, DataCenter
from utils.rpc_func import get_user_current_data_center_id


class DataCenterFloorModule(ModuleBasic):
    """数据中心楼层"""

    @staticmethod
    def get_building_by_id(building_id):
        building = DataCenterBuilding.query.filter(DataCenterBuilding.id == building_id,
                                                   DataCenterBuilding.is_delete == IsDelete.NORMAL).first()
        return building

    @staticmethod
    def get_floor_by_id(floor_id):
        floor = DataCenterFloor.query.filter(DataCenterFloor.id == floor_id,
                                             DataCenterFloor.is_delete == IsDelete.NORMAL).first()
        return floor

    @request_url(DataCenterAddFloorSchema)
    def add_floor(self, form_data):
        building = self.get_building_by_id(form_data["building_id"])
        if not building:
            return self.report.error("找不到相关的楼栋")
        old_floor = DataCenterFloor.query.filter(DataCenterFloor.data_center_building_id == building.id,
                                                 DataCenterFloor.code == form_data["code"],
                                                 DataCenterFloor.is_delete == IsDelete.NORMAL).first()
        if old_floor:
            return self.report.error("楼层编码重复~")
        new_floor = DataCenterFloor()
        new_floor.name = form_data["name"]
        new_floor.code = form_data["code"]
        new_floor.introduction = form_data["introduction"]
        new_floor.cabinet_num = form_data["cabinet_num"]
        new_floor.structure_diagram = form_data["structure_diagram"]
        new_floor.plan = form_data["plan"]
        new_floor.data_center_building_id = building.id
        db.session.add(new_floor)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(DataCenterFloorViewSchema)
    def view_floor(self, form_data):
        building = self.get_building_by_id(form_data["building_id"])
        if not building:
            return self.report.error("找不到相关的楼栋")
        floors = DataCenterFloor.query.filter_by(data_center_building_id=form_data["building_id"]).order_by(
            DataCenterFloor.id.desc()).paginate(form_data["page"],
                                                form_data["size"])
        resp_data = []
        for item in floors.items:
            floor_data = {
                "id": item.id,
                "name": item.name,
                "code": item.code,
                "cabinet_num": item.cabinet_num,
                "introduction": item.introduction,
                "plan": item.plan,
                "structure_diagram": item.structure_diagram,
            }
            resp_data.append(floor_data)
        return self.report.table(resp_data, floors.total)

    @request_url(DataCenterFloorSimpleViewSchema)
    def view_floor_simple(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        data_center = DataCenter.query.filter_by(id=data_center_id).first()
        resp_data = []
        for building in data_center.building_set:
            building_data = {
                "id": building.id,
                "name": building.name,
                "floors": []
            }
            for floor in building.floor_set:
                floor_data = {
                    "id": floor.id,
                    "name": floor.name
                }
                building_data["floors"].append(floor_data)
            resp_data.append(building_data)

        return self.report.post(resp_data)

    @request_url(DataCenterFloorViewFromBuildingIDSchema)
    def view_floor_from_building_id(self, form_data):
        dcf_set = DataCenterFloor.query.filter_by(data_center_building_id=form_data["data_center_building_id"]).all()
        resp_data = []
        for floor in dcf_set:
            floor_data = {
                "id": floor.id,
                "name": floor.name,
                "code": floor.code
            }
            resp_data.append(floor_data)
        return self.report.post(resp_data)

    @request_url(DataCenterUpdateFloorSchema)
    def update_floor(self, form_data):
        floor = self.get_floor_by_id(form_data["id"])
        if not floor:
            return self.report.error("相关楼层不存在")
        if floor.code != form_data["code"]:
            old_floor = DataCenterFloor.query.filter(
                DataCenterFloor.data_center_building_id == floor.data_center_building_id,
                DataCenterFloor.code == form_data["code"]).first()
            if old_floor:
                return self.report.error("楼层数重复")
        floor.name = form_data["name"]
        floor.code = form_data["code"]
        floor.introduction = form_data["introduction"]
        floor.cabinet_num = form_data["cabinet_num"]
        floor.plan = form_data["plan"]
        floor.structure_diagram = form_data["structure_diagram"]
        db.session.add(floor)
        db.session.commit()
        return self.report.suc("更新成功")


dc_floor_module = DataCenterFloorModule()