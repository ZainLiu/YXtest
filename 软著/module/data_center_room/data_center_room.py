from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.data_center.schema import DataCenterAddRoomSchema, DataCenterViewRoomSchema, \
    DataCenterUpdateRoomSchema, DataCenterViewRoomWithDCIDSchema
from models import IsDelete, db
from models.data_center import DataCenterFloor, DataCenterRoom, DataCenter
from utils.rpc_func import get_user_current_data_center_id


class DataCenterRoomModule(ModuleBasic):
    """数据中心房间"""

    @request_url(DataCenterAddRoomSchema)
    def add_room(self, form_data):
        floor = DataCenterFloor.query.filter_by(id=form_data["data_center_floor_id"], is_delete=IsDelete.NORMAL).first()
        if not floor:
            return self.report.error("相关楼层不存在")
        old_record = DataCenterRoom.query.filter_by(data_center_floor_id=floor.id, code=form_data["code"],
                                                    is_delete=IsDelete.NORMAL,
                                                    room_type_id=form_data["room_type_id"]).first()
        if old_record:
            return self.report.error("房间编码重复~")
        room = DataCenterRoom()
        room.data_center_floor_id = floor.id
        room.code = form_data["code"]
        room.name = form_data["name"]
        room.room_type_id = form_data["room_type_id"]
        room.area = form_data["area"]
        room.introduction = form_data["introduction"]
        db.session.add(room)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(DataCenterViewRoomSchema)
    def view_room(self, form_data):
        floor = DataCenterFloor.query.filter_by(id=form_data["data_center_floor_id"], is_delete=IsDelete.NORMAL).first()
        if not floor:
            return self.report.error("相关楼层不存在")
        rooms = DataCenterRoom.query.filter_by(data_center_floor_id=floor.id, is_delete=IsDelete.NORMAL).order_by(
            DataCenterRoom.id.desc()).paginate(form_data["page"],
                                               form_data["size"])
        resp_data = []
        building = floor.data_center_building
        data_center = building.data_center
        country = data_center.country
        province = data_center.province
        full_name_pre = f"{data_center.company.name}-{country.name}-{province.name}-{data_center.name}-{building.name}-{floor.name}-"
        full_code_pre = f"{data_center.company.code}-{country.code}-{province.code}-{data_center.code}-{building.code}-{floor.code}-"
        for item in rooms.items:
            room_data = {
                "id": item.id,
                "name": item.name,
                "code": item.code,
                "room_type_id": item.room_type.id,
                "room_type_name": item.room_type.name,
                "room_type_code": item.room_type.code,
                "area": item.area,
                "introduction": item.introduction,
                "full_name": full_name_pre + f"{item.room_type.name}-{item.name}",
                "full_code": full_code_pre + f"{item.room_type.code}{item.code}"
            }
            resp_data.append(room_data)
        return self.report.table(resp_data, rooms.total)

    @request_url(DataCenterViewRoomSchema)
    def view_room_simple(self, form_data):
        floor = DataCenterFloor.query.filter_by(id=form_data["data_center_floor_id"], is_delete=IsDelete.NORMAL).first()
        if not floor:
            return self.report.error("相关楼层不存在")
        rooms = DataCenterRoom.query.filter_by(data_center_floor_id=floor.id, is_delete=IsDelete.NORMAL).order_by(
            DataCenterRoom.id.desc())
        resp_data = []
        for item in rooms:
            room_data = {
                "id": item.id,
                "name": item.name,
                "code": item.code,
            }
            resp_data.append(room_data)
        return self.report.post(resp_data)

    @request_url(DataCenterViewRoomWithDCIDSchema)
    def view_room_simple_all(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        data_center = DataCenter.query.filter_by(id=data_center_id).first()
        resp_data = []
        for building in data_center.building_set:
            building_data = {
                "id": building.id,
                "name": building.name,
                "code": building.code,
                "floors": []
            }
            for floor in building.floor_set:
                floor_data = {
                    "id": floor.id,
                    "name": floor.name,
                    "code": floor.code,
                    "rooms": []
                }
                for room in floor.dc_room_set:
                    room_data = {
                        "id": room.id,
                        "name": room.name,
                        "code": room.code
                    }
                    floor_data["rooms"].append(room_data)
                building_data["floors"].append(floor_data)
            resp_data.append(building_data)

        return self.report.post(resp_data)

    @request_url(DataCenterUpdateRoomSchema)
    def update_room(self, form_data):
        room = DataCenterRoom.query.filter_by(id=form_data["id"], is_delete=IsDelete.NORMAL).first()
        if not room:
            return self.report.error("房间不存在~")
        if room.code != form_data["code"]:
            old_record = DataCenterRoom.query.filter_by(data_center_floor_id=room.data_center_floor_id,
                                                        code=form_data["code"], is_delete=IsDelete.NORMAL).all()
            if old_record:
                return self.report.error("编码重复~")

        room.name = form_data["name"]
        room.room_type_id = form_data["room_type_id"]
        room.code = form_data["code"]
        room.area = form_data["area"]
        room.introduction = form_data["introduction"]
        db.session.add(room)
        db.session.commit()
        return self.report.suc("更新成功")


dc_room_module = DataCenterRoomModule()
