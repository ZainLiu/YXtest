from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url
from ly_kernel.utils.AuthKey import Token
from ly_service.request.BaseServiceRPC import BaseServiceRPC

from models import IsDelete, IsActive, YesOrNo
from models.data_center import DataCenter, DataCenterBuilding, DataCenterFloor, DataCenterRoom, RoomType
from model_to_view.data_center.schema import DataCenterAddSchema, DataCenterAddBuildingSchema, DataCenterAddFloorSchema, \
    DataCenterUpdateBuildingSchema, DataCenterUpdateFloorSchema, DataCenterUpdateSchema, DataCenterDeleteSchema, \
    DataCenterActiveSchema, DataCenterBuildingDeleteSchema, DataCenterFloorDeleteSchema, DataCenterViewSchema, \
    DataCenterViewSimpleSchema, DataCenterBuildingViewSchema, DataCenterBuildingSimpleViewSchema, \
    DataCenterFloorViewSchema, DataCenterFloorSimpleViewSchema, DataCenterAddRoomSchema, DataCenterViewRoomSchema, \
    DataCenterUpdateRoomSchema
from models.dictionary import Dictionary, DictionaryType
from models.equipment import EquipmentSystem, EquipmentSubSystem, EquipmentType
from utils.const import DEFAULT_ROOM_TYPE, DEFAULT_EQUIPMENT_INFO

db = LieYingApp.db


class DataCenterModule(ModuleBasic):

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

    def get_user_id(self):
        token = BaseServiceRPC.gettoken()
        token_obj = Token.get_token(token)
        uid = token_obj.uid
        user_name = token_obj.account
        return uid, user_name

    @request_url(DataCenterAddSchema)
    def add(self, form_data):
        uid, user_name = self.get_user_id()

        record = DataCenter.query.filter(DataCenter.code == form_data["code"],
                                         DataCenter.is_delete == IsDelete.NORMAL).first()
        if record:
            return self.report.error("编码重复，请确认后修改~")
        try:
            data_center = DataCenter()
            data_center.name = form_data["name"]
            data_center.code = form_data["code"]
            data_center.address = form_data["address"]
            data_center.company_id = form_data["company_id"]
            data_center.province_id = form_data["province_id"]
            data_center.country_id = form_data["country_id"]
            data_center.introduction = form_data["introduction"]
            data_center.creator_id = uid
            data_center.creator_name = user_name
            db.session.add(data_center)
            db.session.flush()
            # 新增默认数据中心房间类型
            # for item in DEFAULT_ROOM_TYPE:
            #     room_type = RoomType()
            #     room_type.name = item["name"]
            #     room_type.code = item["code"]
            #     room_type.data_center_id = data_center.id
            #     room_type.is_sys_conf = YesOrNo.YES
            #     room_type.is_active = IsActive.Active
            #     db.session.add(room_type)
            # 新增默认设备默认分类类型
            for item in DEFAULT_EQUIPMENT_INFO:
                eq_sys = EquipmentSystem()
                eq_sys.name = item["name"]
                eq_sys.code = item["code"]
                eq_sys.data_center_id = data_center.id
                db.session.add(eq_sys)
                db.session.flush()
                for sub_item in item["equipment_sub_system"]:
                    eq_sub_sys = EquipmentSubSystem()
                    eq_sub_sys.equipment_system_id = eq_sys.id
                    eq_sub_sys.name = sub_item["name"]
                    eq_sub_sys.code = sub_item["code"]
                    eq_sub_sys.is_sys_conf = YesOrNo.YES
                    db.session.add(eq_sub_sys)
                    db.session.flush()
                    for eq_type_item in sub_item["equipment_type"]:
                        eq_type = EquipmentType()
                        eq_type.code = eq_type_item["code"]
                        eq_type.name = eq_type_item["name"]
                        eq_type.equipment_sub_system_id = eq_sub_sys.id
                        eq_type.is_sys_conf = YesOrNo.YES
                        eq_type.extra_field = eq_type_item["extra_fields_info"]
                        db.session.add(eq_type)
        except Exception as e:
            db.session.rollback()
            raise e
        db.session.commit()
        return self.report.suc("新增数据中心成功")

    @request_url(DataCenterUpdateSchema)
    def update(self, form_data):
        data_center = DataCenter.query.filter(DataCenter.id == form_data["id"]).first()
        if not data_center:
            return self.report.error("找不到相关数据中心")
        if data_center.is_active != IsActive.NonActive:
            return self.report.error("已激活或停用数据中心不能编辑")
        if data_center.code != form_data["code"]:
            old_data_center = DataCenter.query.filter(DataCenter.code == form_data["code"],
                                                      DataCenter.is_delete == IsDelete.NORMAL).first()
            if old_data_center:
                return self.report.error("编码重复~")
        data_center.name = form_data["name"]
        data_center.code = form_data["code"]
        data_center.company_id = form_data["company_id"]
        data_center.country_id = form_data["country_id"]
        data_center.province_id = form_data["province_id"]
        data_center.address = form_data["address"]
        data_center.introduction = form_data["introduction"]
        db.session.add(data_center)
        db.session.commit()
        return self.report.suc("修改数据中心成功~")

    @request_url(DataCenterDeleteSchema)
    def delete(self, form_data):
        data_center = DataCenter.query.filter(DataCenter.id == form_data["id"]).first()
        if not data_center:
            return self.report.error("找不到相关数据中心")
        if data_center.is_active != IsActive.NonActive:
            return self.report.error("已激活过的数据中心不能删除")
        data_center.is_delete = IsDelete.Deleted
        db.session.add(data_center)
        db.session.commit()
        return self.report.suc("删除成功~")

    @request_url(DataCenterActiveSchema)
    def active(self, form_data):
        return self.change_status(form_data, IsActive.Active)

    @request_url(DataCenterActiveSchema)
    def disable(self, form_data):
        return self.change_status(form_data, IsActive.Disable)

    def change_status(self, form_data, is_active):
        data_center = DataCenter.query.filter(DataCenter.id == form_data["id"]).first()
        if not data_center:
            return self.report.error("找不到相关数据中心")
        if is_active not in [IsActive.Active, IsActive.Disable]:
            return self.report.error("状态参数is_active非法")
        data_center.is_active = is_active
        db.session.add(data_center)
        db.session.commit()
        return self.report.suc(f"{IsActive.CN_NAME[is_active]}成功~")

    @request_url(DataCenterBuildingDeleteSchema)
    def delete_building(self, form_data):
        building = self.get_building_by_id(form_data["building_id"])
        if not building:
            return self.report.error("相关楼栋不存在")
        building.is_delete = IsDelete.Deleted
        db.session.add(building)
        db.session.commit()
        return self.report.suc("楼栋删除成功~")

    @request_url(DataCenterFloorDeleteSchema)
    def delete_floor(self, form_data):
        floor = self.get_floor_by_id(form_data["floor_id"])
        if not floor:
            return self.report.error("相关楼层不存在")
        floor.is_delete = IsDelete.Deleted
        db.session.add(floor)
        db.session.commit()
        return self.report.suc("楼层删除成功~")

    @request_url(DataCenterViewSchema)
    def view(self, form_data):
        filter_cond = [DataCenter.is_delete == IsDelete.NORMAL]
        if form_data["name"]:
            filter_cond.append(DataCenter.name.like(f"%{form_data['name']}%"))
        page_data = DataCenter.query.filter(*filter_cond).order_by(DataCenter.id.desc()).paginate(form_data["page"],
                                                                                                  form_data["size"])
        resp_data = []
        for item in page_data.items:
            center_data = {
                "id": item.id,
                "name": item.name,
                "company": item.company.name,
                "company_id": item.company.id,
                "company_code": item.company.code,
                "country": item.country.name,
                "country_id": item.country.id,
                "country_code": item.country.code,
                "province": item.province.name,
                "province_id": item.province.id,
                "province_code": item.province.code,
                "address": item.address,
                "code": item.code,
                "introduction": item.introduction,
                "is_active": item.is_active,
            }
            resp_data.append(center_data)
        return self.report.table(resp_data, page_data.total)

    @request_url(DataCenterViewSimpleSchema)
    def view_simple(self, form_data):
        filter_cond = [DataCenter.is_active == IsActive.Active]
        if form_data["name"]:
            filter_cond.append(DataCenter.name.like(f"%{form_data['name']}%"))
        data_centers = DataCenter.query.filter(*filter_cond).all()
        resp_data = []
        for data_center in data_centers:
            data_center_simple_info = {
                "id": data_center.id,
                "name": data_center.name,
            }
            # for building in data_center.building_set:
            #     if building.is_delete == IsDelete.Deleted:
            #         continue
            #     building_data = {
            #         "building_id": building.id,
            #         "building_no": building.building_no,
            #         "floor_info": []
            #     }
            #     for floor in building.floor_set:
            #         if floor.is_delete == IsDelete.Deleted:
            #             continue
            #         floor_data = {
            #             "floor_id": floor.id,
            #             "floor_no": floor.floor_no
            #         }
            #         building_data["floor_info"].append(floor_data)
            #     data_center_simple_info["building_info"].append(building_data)
            resp_data.append(data_center_simple_info)
        return self.report.post(resp_data)


data_center_module = DataCenterModule()
