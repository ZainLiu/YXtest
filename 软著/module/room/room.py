from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url

from models import IsDelete, db, IsActive
from models.data_center import DataCenterFloor, DataCenter
from models.dictionary import Dictionary
from models.room import Room
from models.space import Space
from model_to_view.room.schema import RoomAddSchema, RoomAddBatchSchema, RoomDeleteSchema, RoomUpdateSchema, \
    RoomActiveSchema, RoomViewSchema, RoomViewSimpleSchema


class RoomModule(ModuleBasic):

    @request_url(RoomAddSchema)
    def add(self, form_data):
        floor = DataCenterFloor.query.filter(DataCenterFloor.id == form_data["floor_id"],
                                             DataCenterFloor.is_delete == IsDelete.NORMAL).first()
        if not floor:
            return self.report.error("没有相关楼层信息")

        space = Space.query.filter(Space.id == form_data["space_id"], Space.is_delete == IsDelete.NORMAL).first()
        if not space:
            return self.report.error("没有相关楼层信息")

        redis_key = f"add_room_{floor.id}_{space.id}"
        if not LieYingApp.redis.setnx(redis_key, 1):
            return self.report.error("操作过于频繁或者已有其他人在操作，请稍后再试")
        try:

            last_room = Room.query.filter(Room.floor_id == floor.id, Room.space_id == space.id,
                                          Room.is_delete == IsDelete.NORMAL).order_by(
                Room.room_no.desc()).first()
            if last_room:
                new_no = last_room.room_no + 1
            else:
                new_no = 1
            new_room = Room()
            new_room.space_id = space.id
            new_room.floor_id = floor.id
            new_room.room_no = new_no
            new_room.name = form_data["name"]
            db.session.add(new_room)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.commit()
            LieYingApp.redis.delete(redis_key)
            return self.report.error(f"新增失败：{str(e)}")
        LieYingApp.redis.delete(redis_key)
        return self.report.suc("新增房间成功")

    @request_url(RoomAddBatchSchema)
    def add_batch(self, form_data):
        floor = DataCenterFloor.query.filter(DataCenterFloor.id == form_data["floor_id"],
                                             DataCenterFloor.is_delete == IsDelete.NORMAL).first()
        if not floor:
            return self.report.error("没有相关楼层信息")

        space = Space.query.filter(Space.id == form_data["space_id"], Space.is_delete == IsDelete.NORMAL).first()
        if not space:
            return self.report.error("没有相关楼层信息")
        redis_key = f"add_room_{floor.id}_{space.id}"
        status = LieYingApp.redis.setnx(redis_key, 1)
        LieYingApp.redis.expire(redis_key, 5)
        if not status:
            return self.report.error("操作过于频繁或者已有其他人在操作，请稍后再试")
        try:
            last_room = Room.query.filter(Room.floor_id == floor.id, Room.space_id == space.id,
                                          Room.is_delete == IsDelete.NORMAL).order_by(
                Room.room_no.desc()).first()

            if last_room:
                last_room_no = last_room.room_no
            else:
                last_room_no = 0
            new_no_list = [last_room_no + no for no in range(1, form_data["num"] + 1)]

            for new_no in new_no_list:
                new_room = Room()
                new_room.space_id = space.id
                new_room.floor_id = floor.id
                new_room.room_no = new_no
                db.session.add(new_room)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.commit()
            LieYingApp.redis.delete(redis_key)
            return self.report.error(f"新增失败：{str(e)}")
        LieYingApp.redis.delete(redis_key)
        return self.report.suc("新增房间成功")

    @request_url(RoomDeleteSchema)
    def delete(self, form_data):
        room = Room.query.filter(Room.id == form_data["id"], Room.is_delete == IsDelete.NORMAL).first()
        if not room:
            return self.report.error("查询不到相关的房间信息")
        if room.is_active == IsActive.Active:
            return self.report.error("激活中的房间信息不允许删除")
        room.is_delete = IsDelete.Deleted
        db.session.add(room)
        db.session.commit()
        return self.report.suc("房间删除成功")

    @request_url(RoomUpdateSchema)
    def update(self, form_data):
        room = Room.query.filter(Room.id == form_data["id"], Room.is_delete == IsDelete.NORMAL).first()
        if not room:
            return self.report.error("查询不到相关的房间信息")
        if room.is_active == IsActive.Active:
            return self.report.error("激活中的房间信息不允许修改")

        room.name = form_data["name"]
        db.session.add(room)
        db.session.commit()
        return self.report.suc("房间修改成功")

    @request_url(RoomActiveSchema)
    def active(self, form_data):
        room = Room.query.filter(Room.id == form_data["id"], Room.is_delete == IsDelete.NORMAL).first()
        if not room:
            return self.report.error("查询不到相关的房间信息")
        room.is_active = form_data["is_active"]
        db.session.add(room)
        db.session.commit()
        return self.report.suc(f"房间{IsActive.CN_NAME.get(form_data['is_active'])}成功")

    @request_url(RoomViewSchema)
    def view(self, form_data):
        data_center = DataCenter.query.filter(DataCenter.id == form_data["data_center_id"]).first()
        if not data_center:
            return self.report.error("找不到相关的数据中心")
        filter_cond = [Room.is_delete == IsDelete.NORMAL]
        if form_data["name"]:
            filter_cond.append(Room.name.like(f"%{form_data['name']}%"))
        if form_data["is_active"] is not None:
            filter_cond.append(Room.is_active == form_data["is_active"])
        rooms = Room.query.filter(*filter_cond).order_by(Room.id.desc()).paginate(form_data["page"], form_data["size"])
        resp_data = []
        for room in rooms.items:
            resp_data.append({
                "id": room.id,
                "name": room.name,
                "is_active": room.is_active,
                "floor_no": room.floor.floor_no,
                "floor_id": room.floor.id,
                "building_no": room.floor.data_center_building.building_no,
                "building_id": room.floor.data_center_building.id,
                "space_name": room.space.name,
                "space_id": room.space.id,
            })
        return self.report.table(resp_data, rooms.total)

    @request_url(RoomViewSimpleSchema)
    def view_simple(self, form_data):
        data = Dictionary.query.filter(Dictionary.code == "KJGL",
                                       Dictionary.is_delete == IsDelete.NORMAL).first()
        if not data:
            return self.report.error("查找不到相关数据")
        data_subs = Dictionary.query.filter(Dictionary.parent_id == data.id,
                                            Dictionary.is_delete == IsDelete.NORMAL).all()
        resp_data = []
        for data_sub in data_subs:
            sub_data = {
                "id": data_sub.id,
                "name": data_sub.name,
                "sub_info": []
            }
            spaces = Space.query.filter(Space.space_area_id == data_sub.id, Space.is_active == IsActive.Active).all()
            for space in spaces:
                space_data = {
                    "id": space.id,
                    "name": space.name,
                    "sub_info": []
                }

                rooms = Room.query.filter(Room.space_id == space.id, Room.is_active == IsActive.Active,
                                          Room.floor_id == form_data["floor_id"]).all()
                for room in rooms:
                    space_data["sub_info"].append({
                        "id": room.id,
                        "name": room.name
                    })
                sub_data["sub_info"].append(space_data)
            resp_data.append(sub_data)

        return self.report.post(resp_data)


room_module = RoomModule()
