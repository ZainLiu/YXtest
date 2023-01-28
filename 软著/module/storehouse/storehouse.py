from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.storehouse.schema import *
from models import db, IsDelete
from models.storehouse import StoreHouse, GoodShelf, GoodShelfFloor
from sqlalchemy.orm import joinedload

from utils.rpc_func import get_user_current_data_center_id


class StoreHouseModule(ModuleBasic):

    @request_url(StoreHouseCreateSchema)
    def sh_create(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        old_record = StoreHouse.query.filter_by(name=form_data["name"], type=form_data["type"],
                                                data_center_room_id=form_data["data_center_room_id"],
                                                is_delete=IsDelete.NORMAL).first()
        if old_record:
            return self.report.error("在该房间下已经有相同客户相同类型的房间")

        sh = StoreHouse()
        sh.name = form_data["name"]
        sh.type = form_data["type"]
        sh.data_center_id = data_center_id
        sh.data_center_building_id = form_data["data_center_building_id"]
        sh.data_center_floor_id = form_data["data_center_floor_id"]
        sh.data_center_room_id = form_data["data_center_room_id"]
        sh.mark = form_data["mark"]
        sh.creator_id = g.uid
        sh.creator_name = g.account
        db.session.add(sh)
        db.session.commit()
        return self.report.suc("新增仓库成功")

    @request_url(StoreHouseUpdateSchema)
    def sh_update(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        sh = StoreHouse.query.filter_by(id=form_data["id"]).first()
        if not sh:
            return self.report.error("相关数据不存在")
        if sh.name != form_data["name"]:
            old_record = StoreHouse.query.filter_by(name=form_data["name"], type=form_data["type"],
                                                    data_center_room_id=form_data["data_center_room_id"],
                                                    is_delete=IsDelete.NORMAL).first()
            if old_record:
                return self.report.error("该客户在该房间下已有想同类型的仓库")
        sh.name = form_data["name"]
        sh.type = form_data["type"]
        sh.data_center_id = data_center_id
        sh.data_center_building_id = form_data["data_center_building_id"]
        sh.data_center_floor_id = form_data["data_center_floor_id"]
        sh.data_center_room_id = form_data["data_center_room_id"]
        sh.mark = form_data["mark"]
        db.session.add(sh)
        db.session.commit()
        return self.report.suc("更新仓库成功")

    @request_url(StoreHouseListSchema)
    def sh_list(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        sh_set = StoreHouse.query.filter_by(data_center_id=data_center_id, is_delete=IsDelete.NORMAL).all()
        resp_data = []
        for sh in sh_set:
            resp_data.append({
                "id": sh.id,
                "name": sh.name,
            })
        return self.report.post(resp_data)

    @request_url(StoreHouseDeleteSchema)
    def sh_delete(self, form_data):
        sh = StoreHouse.query.filter(StoreHouse.id == form_data["id"]).first()
        if not sh:
            return self.report.error("相关数据不存在")
        sh.is_delete = 1
        db.session.add(sh)
        db.session.commit()
        return self.report.suc("删除仓库成功")

    @request_url(StoreHouseDetailSchema)
    def sh_detail(self, form_data):
        sh = StoreHouse.query.options(joinedload(StoreHouse.data_center),
                                      joinedload(StoreHouse.data_center_building),
                                      joinedload(StoreHouse.data_center_floor),
                                      joinedload(StoreHouse.data_center_room)).filter(
            StoreHouse.id == form_data["id"]).first()
        if not sh:
            return self.report.error("相关数据不存在")
        resp_data = {
            "id": sh.id,
            "name": sh.name,
            "type": sh.type,
            "data_center_name": sh.data_center.name,
            "data_center_id": sh.data_center_id,
            "data_center_building_id": sh.data_center_building_id,
            "data_center_building_name": sh.data_center_building.name,
            "data_center_floor_id": sh.data_center_floor_id,
            "data_center_floor_name": sh.data_center_floor.name,
            "data_center_room_id": sh.data_center_room_id,
            "data_center_room_name": sh.data_center_room.name,
            "creator_id": sh.creator_id,
            "creator_name": sh.creator_name,
            "mark": sh.mark,
            "create_time": sh.create_time.strftime(current_app.config['APP_DATETIME_FORMAT']),
        }
        gs_set = GoodShelf.query.filter_by(store_house_id=sh.id, is_delete=IsDelete.NORMAL).all()
        gs_info = []
        for gs in gs_set:
            gs_data = {
                "id": gs.id,
                "name": gs.name,
                "mark": gs.mark,
                "gsf_info": []
            }
            for gsf in gs.good_shelf_floor_set.filter_by(is_delete=IsDelete.NORMAL).all():
                gs_data["gsf_info"].append({
                    "id": gsf.id,
                    "name": gsf.name,
                    "mark": gsf.mark
                })
            gs_info.append(gs_data)
        resp_data["gs_info"] = gs_info

        return self.report.post(resp_data)

    @request_url(GoodShelfCreateSchema)
    def gs_create(self, form_data):
        old_record = GoodShelf.query.filter_by(store_house_id=form_data["store_house_id"], name=form_data["name"],
                                               is_delete=IsDelete.NORMAL).first()
        if old_record:
            return self.report.error("该仓库已有同名货架")
        gs = GoodShelf()
        gs.name = form_data["name"]
        gs.store_house_id = form_data["store_house_id"]
        gs.mark = form_data["mark"]
        gs.creator_id = g.uid
        gs.creator_name = g.account
        db.session.add(gs)
        db.session.commit()
        return self.report.post({"id": gs.id, "mark": gs.mark, "name": gs.name})

    @request_url(GoodShelfUpdateSchema)
    def gs_update(self, form_data):
        gs = GoodShelf.query.filter_by(id=form_data["id"]).first()
        if not gs:
            return self.report.error("需要修改的数据不存在")
        if gs.name != form_data["name"]:
            old_record = GoodShelf.query.filter_by(name=form_data["name"], store_house_id=gs.store_house_id,
                                                   is_delete=IsDelete.NORMAL).all()
            if old_record:
                return self.report.error("该仓库已有同名货架")
        gs.name = form_data["name"]
        gs.mark = form_data["mark"]
        db.session.add(gs)
        db.session.commit()
        return self.report.post({"id": gs.id, "mark": gs.mark, "name": gs.name})

    @request_url(GoodShelfFloorCreateSchema)
    def gsf_create(self, form_data):
        old_record = GoodShelfFloor.query.filter_by(good_shelf_id=form_data["good_shelf_id"], name=form_data["name"],
                                                    is_delete=IsDelete.NORMAL).first()
        if old_record:
            return self.report.error("该货架已有同名层级")
        gsf = GoodShelfFloor()
        gsf.name = form_data["name"]
        gsf.mark = form_data["mark"]
        gsf.good_shelf_id = form_data["good_shelf_id"]
        gsf.creator_id = g.uid
        gsf.creator_name = g.account
        db.session.add(gsf)
        db.session.commit()
        return self.report.post({"id": gsf.id, "mark": gsf.mark, "name": gsf.name})

    @request_url(GoodShelfFloorUpdateSchema)
    def gsf_update(self, form_data):
        gsf = GoodShelfFloor.query.filter_by(id=form_data["id"]).first()
        if not gsf:
            return self.report.error("需要变更的数据不存在")

        if gsf.name != form_data["name"]:
            old_record = GoodShelfFloor.query.filter_by(name=form_data["name"], good_shelf_id=gsf.good_shelf_id,
                                                        is_delete=IsDelete.NORMAL).all()
            if old_record:
                return self.report.error("该货架已有同名货架层")
        gsf.name = form_data["name"]
        gsf.mark = form_data["mark"]
        db.session.add(gsf)
        db.session.commit()
        return self.report.post({"id": gsf.id, "mark": gsf.mark, "name": gsf.name})


sh_module = StoreHouseModule()
