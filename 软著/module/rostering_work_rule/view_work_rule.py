from flask import g, request
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc
from model_to_view.rostering_work_rule.serializer import WorkRuleListSerialize
from model_to_view.rostering_work_rule.schema import WorkRuleListSchema, WorkRuleCreateSchema, WorkRuleUpdateSchema, \
    WorkRuleActiveSchema, WorkRuleDetailByIdSchema
from models import IsValid, OperationType, IsActive
from models.rostering.work_rule import WorkRule, WorkRuleDetail
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id


class WorkRuleModule(ModuleBasic):
    """排班规则"""

    @request_url(WorkRuleListSchema)
    def work_rule_list(self, form_data):
        """查询排班规则列表"""
        id = form_data.get('id')
        name = form_data.get('name')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [WorkRule.data_center_id == data_center_id]
        if id:
            query_list.append(WorkRule.id == id)
        if name:
            query_list.append(WorkRule.name.like(f'%{name}%'))

        work_rule_set = WorkRule.query.filter(*query_list).order_by(desc(WorkRule.id))
        count = work_rule_set.count()
        work_rule_set = work_rule_set.paginate(page, size)

        data = WorkRuleListSerialize(many=True).dump(work_rule_set.items)

        return self.report.table(*(data, count))

    @request_url(WorkRuleDetailByIdSchema)
    def work_rule_detail(self, form_data):
        """获取排班规则详情"""
        id = form_data.get('id')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            WorkRule.data_center_id == data_center_id,
            WorkRule.id == id
        ]

        work_rule = WorkRule.query.filter(*query_list).first()
        if not work_rule:
            return self.report.error("找不到该id的排班规则")

        data = WorkRuleListSerialize().dump(work_rule)

        return self.report.post(data)

    @request_url(WorkRuleCreateSchema)
    def work_rule_create(self, form_data):
        """新增排班规则"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()

        rule_detail_set = form_data.pop('rule_detail_set')
        try:
            instance = WorkRule(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建规则明细
            for detail in rule_detail_set:
                detail.pop('operation')
                detail['id'] = None
                detail['rule_id'] = instance.id

                detail_instance = WorkRuleDetail(**detail)
                LieYingApp.db.session.add(detail_instance)
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('新增排班规则成功')

    @request_url(WorkRuleUpdateSchema)
    def work_rule_update(self, form_data):
        """修改排班规则"""
        group_set = WorkRule.query.filter_by(id=form_data['id'])
        instance = group_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的客户')

        rule_detail_set = form_data.pop('rule_detail_set')
        try:
            group_set.update(form_data)
            LieYingApp.db.session.flush()

            # 创建规则明细
            for detail in rule_detail_set:
                operation = detail.pop('operation')
                if operation == OperationType.ADD:
                    detail['id'] = None
                    detail['rule_id'] = instance.id

                    detail_instance = WorkRuleDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)
                elif operation == OperationType.UPDATE:
                    WorkRuleDetail.query.filter_by(id=detail['id']).update(detail)
                elif operation == operation == OperationType.DELETE:
                    WorkRuleDetail.query.filter_by(id=detail['id']).delete()

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('修改排班规则成功')

    @request_url(WorkRuleActiveSchema)
    def work_rule_active(self, form_data):
        """激活/停用排班规则"""
        work_type_set = WorkRule.query.filter_by(id=form_data['id'])
        instance = work_type_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的客户')
        try:
            work_type_set.update(form_data)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('成功')

    def work_rule_easy(self):
        """获取排班规则简单列表"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        query_list = [WorkRule.data_center_id == data_center_id, WorkRule.is_active == IsActive.Active]
        work_rule_set = WorkRule.query.filter(*query_list).order_by(desc(WorkRule.id))

        result = []
        for work_rule in work_rule_set:
            rule_detail_set = work_rule.rule_detail_set
            work_type_list = []

            for detail in rule_detail_set:
                if not hasattr(detail, 'work_type'):
                    continue
                work_type_list.append({
                    'id': detail.work_type.id,
                    'name': detail.work_type.name,
                    'type': detail.work_type.type,
                    'style_type': detail.work_type.style_type
                })

            result.append({
                'id': work_rule.id,
                'name': work_rule.name,
                'weekend_valid':work_rule.weekend_valid,
                'work_type_list': work_type_list
            })

        return self.report.post(result)


work_rule_module = WorkRuleModule()
