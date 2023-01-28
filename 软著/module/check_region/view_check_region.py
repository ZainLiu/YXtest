from flask import g
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc

from model_to_view.check_patrol_project.serializer import CheckPatrolProjectListSerialize
from model_to_view.check_region.schema import CheckRegionListSchema, CheckRegionCreateSchema, CheckRegionUpdateSchema, \
    CheckRegionFlowSchema, CheckRegionActiveSchema, CheckRegionUpdateVersionSchema, CheckRegionGetProjectSchema, \
    CheckRegionDetailByIdSchema
from model_to_view.check_region.serializer import CheckRegionListSerialize, CheckRegionByIdSerialize
from models.check.check_region import CheckRegion, CheckRegionDetail
from models import IsValid, OperationType, IsActive
from models.check.check_patrol_project import CheckPatrolProject, CheckPatrolProjectDetail, CheckType
from module.check_region.flow_service import FlowServiceCheckRegion
from utils import create_or_update_detail
from utils.flow_decorator import flow_decorator
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id, get_user_list_by_data_center_id


class CheckRegionModule(ModuleBasic):
    """巡检区域"""

    @request_url(CheckRegionListSchema)
    def check_region_list(self, form_data):
        """查询巡检区域列表"""
        serial_number = form_data.get('serial_number')
        data_center_building_id = form_data.get('data_center_building_id')
        data_center_floor_id = form_data.get('data_center_floor_id')
        data_center_room_id = form_data.get('data_center_room_id')
        title = form_data.get('title')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckRegion.data_center_id == data_center_id]
        if title:
            query_list.append(CheckRegion.title.like(f'%{title}%'))
        if serial_number:
            query_list.append(CheckRegion.serial_number.like(f'%{serial_number}%'))
        if data_center_building_id and data_center_floor_id and data_center_room_id:
            query_list.append(CheckRegion.data_center_building_id == data_center_building_id)
            query_list.append(CheckRegion.data_center_floor_id == data_center_floor_id)
            query_list.append(CheckRegion.data_center_room_id == data_center_room_id)

        region_set = CheckRegion.query.filter(*query_list).order_by(desc(CheckRegion.id))
        count = region_set.count()
        region_set = region_set.paginate(page, size)

        data = CheckRegionListSerialize(many=True).dump(region_set.items)

        return self.report.table(*(data, count))

    @request_url(CheckRegionDetailByIdSchema)
    def check_region_detail(self, form_data):
        """获取巡检区域明细"""
        id = form_data.get('id')
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckRegion.data_center_id == data_center_id]
        if id:
            query_list.append(CheckRegion.id == id)

        project = CheckRegion.query.filter(*query_list).first()
        if not project:
            return self.report.error("找不到该id的巡检区域")

        data = CheckRegionByIdSerialize().dump(project)

        return self.report.post(data)

    @request_url(CheckRegionCreateSchema)
    def check_region_create(self, form_data):
        """新增巡检区域"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(CheckRegion, 'XJQY')

        equipment_detail_set = form_data.pop('equipment_detail_set')
        environment_detail_set = form_data.pop('environment_detail_set')
        try:
            instance = CheckRegion(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 新增或修改设备明细
            if equipment_detail_set:
                for detail in equipment_detail_set:
                    detail['check_patrol_project_type'] = CheckType.Equipment

            # 新增或修改环境明细
            if environment_detail_set:
                for detail in environment_detail_set:
                    detail['check_patrol_project_type'] = CheckType.Environment

            detail_list = equipment_detail_set + environment_detail_set
            create_or_update_detail('check_region_id', CheckRegionDetail, instance.id, detail_list)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('新增巡检区域成功')

    @request_url(CheckRegionUpdateSchema)
    def check_region_update(self, form_data):
        """修改巡检区域"""
        region_set = CheckRegion.query.filter_by(id=form_data['id'])
        instance = region_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检区域')

        equipment_detail_set = form_data.pop('equipment_detail_set')
        environment_detail_set = form_data.pop('environment_detail_set')
        try:
            region_set.update(form_data)
            LieYingApp.db.session.flush()

            # 新增或修改设备明细
            if equipment_detail_set:
                for detail in equipment_detail_set:
                    detail['check_patrol_project_type'] = CheckType.Equipment

            # 新增或修改环境明细
            if environment_detail_set:
                for detail in environment_detail_set:
                    detail['check_patrol_project_type'] = CheckType.Environment

            detail_list = equipment_detail_set + environment_detail_set
            create_or_update_detail('check_region_id', CheckRegionDetail, instance.id, detail_list)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('修改巡检区域成功')

    @request_url(CheckRegionFlowSchema)
    @flow_decorator(FlowServiceCheckRegion)
    def check_region_flow(self, form_data):
        """审批巡检区域"""
        region_set = CheckRegion.query.filter_by(id=form_data['id'])
        instance = region_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检区域')

        g.fid = instance.id
        return self.report.suc('发起审批成功')

    @request_url(CheckRegionActiveSchema)
    def check_region_active(self, form_data):
        """启用某版本"""
        region_set = CheckRegion.query.filter_by(id=form_data['id'])
        instance = region_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检区域')

        try:
            # 先把本单号的所有单置为失效
            all_region_set = CheckRegion.query.filter_by(serial_number=instance.serial_number)
            all_region_set.update({'is_active': IsActive.Disable})

            # 接着更新本单为激活
            region_set.update({'is_active': IsActive.Active})
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.error('启用版本成功')

    @request_url(CheckRegionUpdateVersionSchema)
    def check_region_update_version(self, form_data):
        """版本更新"""
        id = form_data.pop('id')
        parent_instance = CheckRegion.query.filter_by(id=id).first()
        if not parent_instance:
            return self.report.error('执行更新时找不到对应id的巡检项目')

        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        equipment_detail_set = form_data.pop('equipment_detail_set')
        environment_detail_set = form_data.pop('environment_detail_set')
        form_data['serial_number'] = parent_instance.serial_number
        form_data['version'] = parent_instance.version + 1

        try:
            instance = CheckRegion(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 新增或修改设备明细
            if equipment_detail_set:
                for detail in equipment_detail_set:
                    detail['check_patrol_project_type'] = CheckType.Equipment

            # 新增或修改环境明细
            if environment_detail_set:
                for detail in environment_detail_set:
                    detail['check_patrol_project_type'] = CheckType.Environment

            detail_list = equipment_detail_set + environment_detail_set
            create_or_update_detail('check_region_id', CheckRegionDetail, instance.id, detail_list)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('版本更新')

    @request_url(CheckRegionGetProjectSchema)
    def check_region_get_project(self, form_data):
        """获取巡检项目"""
        check_type = form_data.get('check_type')
        serial_number = form_data.get('serial_number')
        equipment_system_id = form_data.get('equipment_system_id')
        equipment_sub_system_id = form_data.get('equipment_sub_system_id')
        equipment_type_id = form_data.get('equipment_type_id')
        title = form_data.get('title')
        creator_name = form_data.get('creator_name')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            CheckPatrolProject.data_center_id == data_center_id,
            CheckPatrolProject.is_active == IsActive.Active,
            CheckPatrolProject.check_type == check_type
        ]
        if serial_number:
            query_list.append(CheckPatrolProject.serial_number.like(f'%{serial_number}%'))
        if equipment_system_id:
            query_list.append(CheckPatrolProject.equipment_system_id == equipment_system_id)
        if equipment_sub_system_id:
            query_list.append(CheckPatrolProject.equipment_sub_system_id == equipment_sub_system_id)
        if equipment_type_id:
            query_list.append(CheckPatrolProject.equipment_type_id == equipment_type_id)
        if title:
            query_list.append(CheckPatrolProject.title.like(f'%{title}%'))
        if creator_name:
            query_list.append(CheckPatrolProject.creator_name.like(f'%{creator_name}%'))

        project_set = CheckPatrolProject.query.filter(*query_list).order_by(desc(CheckPatrolProject.id))

        data = CheckPatrolProjectListSerialize(many=True).dump(project_set)

        return self.report.post(data)


check_region_module = CheckRegionModule()
