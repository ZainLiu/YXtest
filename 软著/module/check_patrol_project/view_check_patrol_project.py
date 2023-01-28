from flask import g
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc

from model_to_view.check_patrol_project.schema import CheckPatrolProjectListSchema, CheckPatrolProjectCreateSchema, \
    CheckPatrolProjectUpdateSchema, CheckPatrolProjectFlowSchema, CheckPatrolProjectActiveSchema, \
    CheckPatrolProjectUpdateVersionSchema, CheckPatrolProjectDetailByIdSchema
from module.check_patrol_project.flow_service import FlowServiceCheckPatrolProject
from model_to_view.check_patrol_project.serializer import CheckPatrolProjectListSerialize, \
    CheckPatrolProjectByIdSerialize
from models import IsValid, OperationType, IsActive
from models.check.check_patrol_project import CheckPatrolProject, CheckPatrolProjectDetail, CheckType
from utils import create_or_update_detail
from utils.flow_decorator import flow_decorator
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id, get_user_list_by_data_center_id


class CheckPatrolProjectModule(ModuleBasic):
    """巡检项目"""

    @request_url(CheckPatrolProjectListSchema)
    def check_patrol_project_list(self, form_data):
        """查询巡检项目列表"""
        check_type = form_data.get('check_type')
        serial_number = form_data.get('serial_number')
        equipment_system_id = form_data.get('equipment_system_id')
        equipment_sub_system_id = form_data.get('equipment_sub_system_id')
        equipment_type_id = form_data.get('equipment_type_id')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckPatrolProject.data_center_id == data_center_id]
        if check_type:
            query_list.append(CheckPatrolProject.check_type == check_type)
        if serial_number:
            query_list.append(CheckPatrolProject.serial_number.like(f'%{serial_number}%'))
        if equipment_system_id and equipment_sub_system_id and equipment_type_id:
            query_list.append(CheckPatrolProject.equipment_system_id == equipment_system_id)
            query_list.append(CheckPatrolProject.equipment_sub_system_id == equipment_sub_system_id)
            query_list.append(CheckPatrolProject.equipment_type_id == equipment_type_id)

        project_set = CheckPatrolProject.query.filter(*query_list).order_by(desc(CheckPatrolProject.id))
        count = project_set.count()
        project_set = project_set.paginate(page, size)

        data = CheckPatrolProjectListSerialize(many=True).dump(project_set.items)

        return self.report.table(*(data, count))

    @request_url(CheckPatrolProjectDetailByIdSchema)
    def check_patrol_project_detail(self, form_data):
        """获取巡检项目明细"""
        id = form_data.get('id')
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckPatrolProject.data_center_id == data_center_id]
        if id:
            query_list.append(CheckPatrolProject.id == id)

        project = CheckPatrolProject.query.filter(*query_list).first()
        if not project:
            return self.report.error("找不到该id的巡检项目")

        data = CheckPatrolProjectByIdSerialize().dump(project)

        return self.report.post(data)

    @request_url(CheckPatrolProjectCreateSchema)
    def check_patrol_project_create(self, form_data):
        """新增巡检项目"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(CheckPatrolProject, 'XJXM')

        detail_set = form_data.pop('detail_set')
        try:
            instance = CheckPatrolProject(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 新增或修改明细
            create_or_update_detail('check_patrol_project_id', CheckPatrolProjectDetail, instance.id, detail_set)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('新增巡检项目成功')

    @request_url(CheckPatrolProjectUpdateSchema)
    def check_patrol_project_update(self, form_data):
        """修改巡检项目"""
        project_set = CheckPatrolProject.query.filter_by(id=form_data['id'])
        instance = project_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检项目')

        detail_set = form_data.pop('detail_set')
        try:
            project_set.update(form_data)
            LieYingApp.db.session.flush()

            # 新增或修改明细
            create_or_update_detail('check_patrol_project_id', CheckPatrolProjectDetail, instance.id, detail_set)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('修改巡检项目成功')

    @request_url(CheckPatrolProjectFlowSchema)
    @flow_decorator(FlowServiceCheckPatrolProject)
    def check_patrol_project_flow(self, form_data):
        """审批巡检项目"""
        project_set = CheckPatrolProject.query.filter_by(id=form_data['id'])
        instance = project_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检项目')

        g.fid = instance.id
        return self.report.suc('发起审批成功')

    @request_url(CheckPatrolProjectActiveSchema)
    def check_patrol_project_active(self, form_data):
        """启用某版本"""
        project_set = CheckPatrolProject.query.filter_by(id=form_data['id'])
        instance = project_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检项目')

        try:
            # 先把本单号的所有单置为失效
            all_project_set = CheckPatrolProject.query.filter_by(serial_number=instance.serial_number)
            all_project_set.update({'is_active': IsActive.Disable})

            # 接着更新本单为激活
            project_set.update({'is_active': IsActive.Active})
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('启用版本成功')

    @request_url(CheckPatrolProjectUpdateVersionSchema)
    def check_patrol_project_update_version(self, form_data):
        """版本更新"""
        id = form_data.pop('id')
        project_set = CheckPatrolProject.query.filter_by(id=id)
        parent_instance = project_set.first()
        if not parent_instance:
            return self.report.error('执行版本更新时找不到对应id的巡检项目')

        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        detail_set = form_data.pop('detail_set')
        form_data['serial_number'] = parent_instance.serial_number
        form_data['check_type'] = parent_instance.check_type
        form_data['version'] = parent_instance.version + 1

        if parent_instance.check_type == CheckType.Equipment:
            form_data['equipment_system_id'] = parent_instance.equipment_system_id
            form_data['equipment_sub_system_id'] = parent_instance.equipment_sub_system_id
            form_data['equipment_type_id'] = parent_instance.equipment_type_id

        try:
            instance = CheckPatrolProject(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 新增或修改明细
            create_or_update_detail('check_patrol_project_id', CheckPatrolProjectDetail, instance.id, detail_set)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('版本更新')


check_patrol_project_module = CheckPatrolProjectModule()
