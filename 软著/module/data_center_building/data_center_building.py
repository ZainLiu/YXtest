from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.data_center.schema import *
from models import IsDelete, db
from models.data_center import DataCenter, DataCenterBuilding
from utils.rpc_func import get_user_current_data_center_id


class DataCenterBuildingModule(ModuleBasic):
    """数据中心楼宇"""

    @staticmethod
    def get_building_by_id(building_id):
        building = DataCenterBuilding.query.filter(DataCenterBuilding.id == building_id,
                                                   DataCenterBuilding.is_delete == IsDelete.NORMAL).first()
        return building

    @request_url(DataCenterAddBuildingSchema)
    def add_building(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        data_center = DataCenter.query.filter(DataCenter.id == data_center_id,
                                              DataCenter.is_delete == IsDelete.NORMAL).first()
        if not data_center:
            return self.report.error("找不到相关的数据中心")

        old_building = DataCenterBuilding.query.filter(DataCenterBuilding.data_center_id == data_center.id,
                                                       DataCenterBuilding.code == form_data["code"],
                                                       DataCenterBuilding.is_delete == IsDelete.NORMAL).first()
        if old_building:
            return self.report.error("楼栋号码重复")

        new_building = DataCenterBuilding()
        new_building.code = form_data["code"]
        new_building.name = form_data["name"]
        new_building.cabinet_num = form_data["cabinet_num"]
        new_building.introduction = form_data["introduction"]
        new_building.floor_num = form_data["floor_num"]
        new_building.annex = form_data["annex"]
        new_building.data_center_id = data_center.id
        db.session.add(new_building)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(DataCenterBuildingViewSchema)
    def view_building(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        data_center = DataCenter.query.filter(DataCenter.id == data_center_id,
                                              DataCenter.is_delete == IsDelete.NORMAL).first()
        if not data_center:
            return self.report.error("找不到相关的数据中心")
        building_set = DataCenterBuilding.query.filter_by(data_center_id=data_center.id,
                                                          is_delete=IsDelete.NORMAL).order_by(
            DataCenterBuilding.id.desc()).paginate(form_data["page"],
                                                   form_data["size"])

        resp_data = []
        full_code_pre = f"YX-{data_center.country.code}-{data_center.province.code}-{data_center.code}-"
        for item in building_set.items:
            building_data = {
                "id": item.id,
                "name": item.name,
                "code": item.code,
                "floor_num": item.floor_num,
                "data_center_id": data_center.id,
                "data_center_name": data_center.name,
                "full_code": full_code_pre + item.code,
                "annex": item.annex,
                "cabinet_num": item.cabinet_num,
            }
            resp_data.append(building_data)

        return self.report.table(resp_data, building_set.total)

    @request_url(DataCenterBuildingSimpleViewSchema)
    def view_building_simple(self, form_data):
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        data_center = DataCenter.query.filter(DataCenter.id == data_center_id,
                                              DataCenter.is_delete == IsDelete.NORMAL).first()
        if not data_center:
            return self.report.error("找不到相关的数据中心")
        building_set = DataCenterBuilding.query.filter_by(data_center_id=data_center.id,
                                                          is_delete=IsDelete.NORMAL).order_by(
            DataCenterBuilding.id.desc())

        resp_data = []
        for item in building_set:
            building_data = {
                "id": item.id,
                "name": item.name,
            }
            resp_data.append(building_data)

        return self.report.post(resp_data)

    @request_url(DataCenterUpdateBuildingSchema)
    def update_building(self, form_data):
        building = self.get_building_by_id(form_data["id"])
        if not building:
            return self.report.error("相关楼栋不存在")

        if building.code != form_data["code"]:
            old_building = DataCenterBuilding.query.filter(DataCenterBuilding.data_center_id == building.data_center_id,
                                                           DataCenterBuilding.code == form_data[
                                                               "code"],
                                                           DataCenterBuilding.is_delete == IsDelete.NORMAL).first()
            if old_building:
                return self.report.error("楼栋编号重复")
        building.code = form_data["code"]
        building.name = form_data["name"]
        building.cabinet_num = form_data["cabinet_num"]
        building.introduction = form_data["introduction"]
        building.annex = form_data["annex"]
        building.floor_num = form_data["floor_num"]
        db.session.add(building)
        db.session.commit()
        return self.report.suc("更新成功")


dc_building = DataCenterBuildingModule()
