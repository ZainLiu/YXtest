from flask import g
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc

from model_to_view.check_region.serializer import CheckRegionListSerialize
from model_to_view.check_route.schema import CheckRouteListSchema, CheckRouteCreateSchema, \
    CheckRouteUpdateSchema, CheckRouteFlowSchema, CheckRouteActiveSchema, CheckRouteUpdateVersionSchema, \
    CheckRouteGetRegionSchema, CheckRouteDetailByIdSchema
from model_to_view.check_route.serializer import CheckRouteListSerialize, CheckRouteByIdSerialize
from models.check.check_region import CheckRegion
from models import IsValid, OperationType, IsActive
from models.check.check_route import CheckRoute, CheckRouteDetail
from module.check_route.flow_service import FlowServiceCheckRoute
from utils import create_or_update_detail
from utils.flow_decorator import flow_decorator
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id


class CheckRouteModule(ModuleBasic):
    """巡检路线"""

    @request_url(CheckRouteListSchema)
    def check_route_list(self, form_data):
        """查询巡检路线列表"""
        serial_number = form_data.get('serial_number')
        title = form_data.get('title')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckRoute.data_center_id == data_center_id]
        if title:
            query_list.append(CheckRoute.title.like(f'%{title}%'))
        if serial_number:
            query_list.append(CheckRoute.serial_number.like(f'%{serial_number}%'))

        route_set = CheckRoute.query.filter(*query_list).order_by(desc(CheckRoute.id))
        count = route_set.count()
        route_set = route_set.paginate(page, size)

        data = CheckRouteListSerialize(many=True).dump(route_set.items)

        return self.report.table(*(data, count))

    @request_url(CheckRouteDetailByIdSchema)
    def check_region_detail(self, form_data):
        """获取巡检路线明细"""
        id = form_data.get('id')
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckRoute.data_center_id == data_center_id]
        if id:
            query_list.append(CheckRoute.id == id)

        project = CheckRoute.query.filter(*query_list).first()
        if not project:
            return self.report.error("找不到该id的巡检路线")

        data = CheckRouteByIdSerialize().dump(project)

        return self.report.post(data)

    @request_url(CheckRouteCreateSchema)
    def check_route_create(self, form_data):
        """新增巡检路线"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(CheckRoute, 'XJLX')

        detail_set = form_data.pop('detail_set')
        try:
            instance = CheckRoute(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 新增或修改明细
            create_or_update_detail('check_route_id', CheckRouteDetail, instance.id, detail_set)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('新增巡检路线成功')

    @request_url(CheckRouteUpdateSchema)
    def check_route_update(self, form_data):
        """修改巡检路线"""
        route_set = CheckRoute.query.filter_by(id=form_data['id'])
        instance = route_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检路线')

        detail_set = form_data.pop('detail_set')
        try:
            route_set.update(form_data)
            LieYingApp.db.session.flush()

            # 新增或修改明细
            create_or_update_detail('check_route_id', CheckRouteDetail, instance.id, detail_set)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('修改巡检路线成功')

    @request_url(CheckRouteFlowSchema)
    @flow_decorator(FlowServiceCheckRoute)
    def check_route_flow(self, form_data):
        """审批巡检路线"""
        route_set = CheckRoute.query.filter_by(id=form_data['id'])
        instance = route_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检路线')

        g.fid = instance.id
        return self.report.suc('发起审批成功')

    @request_url(CheckRouteActiveSchema)
    def check_route_active(self, form_data):
        """启用某版本"""
        route_set = CheckRoute.query.filter_by(id=form_data['id'])
        instance = route_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的巡检路线')

        try:
            # 先把本单号的所有单置为失效
            all_route_set = CheckRoute.query.filter_by(serial_number=instance.serial_number)
            all_route_set.update({'is_active': IsActive.Disable})

            # 接着更新本单为激活
            route_set.update({'is_active': IsActive.Active})
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('启用版本成功')

    @request_url(CheckRouteUpdateVersionSchema)
    def check_route_update_version(self, form_data):
        """版本更新"""
        id = form_data.pop('id')
        parent_instance = CheckRoute.query.filter_by(id=id).first()
        if not parent_instance:
            return self.report.error('执行更新时找不到对应id的巡检项目')

        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        detail_set = form_data.pop('detail_set')
        form_data['serial_number'] = parent_instance.serial_number
        form_data['version'] = parent_instance.version + 1

        try:
            instance = CheckRoute(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 新增或修改明细
            create_or_update_detail('check_route_id', CheckRouteDetail, instance.id, detail_set)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('版本更新')

    @request_url(CheckRouteGetRegionSchema)
    def check_route_get_region(self, form_data):
        """获取巡检区域"""
        serial_number = form_data.get('serial_number')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            CheckRegion.data_center_id == data_center_id,
            CheckRegion.is_active == IsActive.Active,
        ]
        if serial_number:
            query_list.append(CheckRegion.serial_number.like(f'%{serial_number}%'))

        project_set = CheckRegion.query.filter(*query_list).order_by(desc(CheckRegion.id))

        data = CheckRegionListSerialize(many=True).dump(project_set)

        return self.report.post(data)


check_route_module = CheckRouteModule()
