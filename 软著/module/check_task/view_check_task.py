import datetime

from flask import g
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc, not_, or_, and_

from config import current_config
from model_to_view.check_task.schema import CheckTaskListSchema, CheckTaskDetailByIdSchema, CheckTaskAcceptSchema, \
    CheckTaskGetRouteInfo, CheckTaskGetRegionInfo, CheckTaskPutResult, CheckTaskDone, CheckTaskSuspendSchema
from model_to_view.check_task.serializer import CheckTaskListSerialize
from models import YesOrNo, FlowStatus
from models.check.check_patrol_project import CheckType, DataType, LogicSymbol, RelationSymbol
from models.check.check_region import CheckRegion
from models.check.check_route import CheckRouteDetail
from models.check.check_task import CheckTask, TaskStatus, CheckTaskProjectResult
from models.equipment import Equipment
from models.rostering.work_exchange import WorkExchangeApply, ApplyType
from module.check_task.flow_service import FlowServiceWorkExchange
from module.rostering_people_group.service.people_group_service import PeopleGroupService
from public.work_utils import WorkUtils
from utils.code_util import CodeUtil
from utils.flow_decorator import flow_decorator
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id


class CheckTaskModule(ModuleBasic):
    """巡检任务"""

    @request_url(CheckTaskListSchema)
    def check_task_list(self, form_data):
        serial_number = form_data.get('serial_number')
        date = form_data.get('date')
        group_name = form_data.get('group_name')
        status = form_data.get('status')
        is_timeout = form_data.get('is_timeout')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [CheckTask.data_center_id == data_center_id]
        if serial_number:
            query_list.append(CheckTask.serial_number.like(f'%{serial_number}%'))
        if date:
            query_list.append(CheckTask.date == date)
        if group_name:
            query_list.append(CheckTask.group_name.like(f'%{group_name}%'))
        if status:
            query_list.append(CheckTask.status == status)
        if is_timeout:
            query_list.append(CheckTask.is_timeout == is_timeout)

        task_set = CheckTask.query.filter(*query_list).order_by(desc(CheckTask.id))
        count = task_set.count()
        task_set = task_set.paginate(page, size)

        data = CheckTaskListSerialize(many=True).dump(task_set.items)

        return self.report.table(*(data, count))

    @request_url(CheckTaskDetailByIdSchema)
    def check_task_detail(self, form_data):
        """获取巡检任务详情"""
        id = form_data['id']
        is_ipad = form_data['is_ipad']

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        task_set = CheckTask.query.filter_by(id=id, data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        ret_result = {
            'id': instance.id,
            'serial_number': instance.serial_number,
            'check_route_title': instance.check_route.title,
            'check_route_version': instance.check_route.version,
            'date': instance.date.strftime(current_config.APP_DATE_FORMAT),
            'task_time': f'{instance.task_time_start.strftime(current_config.APP_TIME_FORMAT)}-'
                         f'{instance.task_time_end.strftime(current_config.APP_TIME_FORMAT)}',
            'group_name': instance.group_name,
            'user_id': instance.user_id,
            'user_name': instance.user_name,
            'start_time': instance.start_time.strftime(current_config.APP_DATE_FORMAT),
            'end_time': instance.end_time.strftime(current_config.APP_DATE_FORMAT),
            'is_start': False
        }

        # 检查巡检任务时间是否开始
        now_time = datetime.datetime.now()
        now_date = now_time.strftime(current_config.APP_DATE_FORMAT)
        task_start_time_str = instance.task_time_start.strftime(current_config.APP_TIME_FORMAT)
        task_start_time = datetime.datetime.strptime(f'{now_date} {task_start_time_str}',
                                                     current_config.APP_DATETIME_FORMAT)
        if now_time >= task_start_time:
            ret_result['is_start'] = True

        # 如果是ipad，或者任务未完成，直接返回
        if is_ipad or instance.status != TaskStatus.Done:
            return self.report.post(ret_result)

        # 否则，还需要获取巡检结果的信息
        ret_result['check_result'] = []
        result_set = CheckTaskProjectResult.query.filter_by(check_task_id=instance.id).all()

        # 先把所有设备、巡检区域查出来，存成字典，方便后续取用，不用再多次查询数据库
        equipment_ids, region_ids = [], []
        for result in result_set:
            if result.equipment_id:
                equipment_ids.append(result.equipment_id)
            if result.check_region_id:
                region_ids.append(result.check_region_id)

        equipment_set = Equipment.query.filter(Equipment.id.in_(equipment_ids)).all()
        equipment_dict = {equipment.id: equipment for equipment in equipment_set}

        region_set = CheckRegion.query.filter(CheckRegion.id.in_(region_ids)).all()
        region_dict = {region.id: region for region in region_set}

        # key-区域id value-{'项目id或设备id':{'id':1,'名称':'xxx','巡检项':[]}}
        check_dict = {}
        for result in result_set:
            check_region_id = result.check_region_id
            if not check_dict.get(check_region_id):
                check_dict[check_region_id] = {}
            check_dict[check_region_id] = {}
            equipment_id = result.equipment_id
            check_patrol_project_type = result.check_patrol_project_type
            check_patrol_project_id = result.check_patrol_project_id
            check_patrol_project_detail_id = result.check_patrol_project_detail_id

            if check_patrol_project_type == CheckType.Equipment:
                # 设备
                flag = f'eq_{equipment_id}'
                equipment = equipment_dict.get(equipment_id)
                # 正常不可能找不到设备
                if not equipment:
                    continue
                if not check_dict[check_region_id].get(flag):
                    # 该设备的基本信息
                    check_dict[check_region_id][flag] = {
                        'check_id': equipment.id,
                        'title': result.check_patrol_project.title,
                        'code': equipment.code,
                        'full_code': CodeUtil.get_eq_full_code(equipment),
                        'is_equipment': YesOrNo.YES,
                        'check_region_id': check_region_id,
                        'check_patrol_project_id': check_patrol_project_id,
                        'check_patrol_project_detail_id': check_patrol_project_detail_id,
                        'content': []
                    }

                # 具体巡检内容
                check_dict[check_region_id][flag]['content'].append({
                    'result_id': result.id,
                    'value': result.value,
                    'check_detail_type': result.check_patrol_project_detail.type,
                    'check_detail_title': result.check_patrol_project_detail.title,
                    'check_detail_warn_rule': result.check_patrol_project_detail.warn_rule,
                    'check_detail_check_rule': result.check_patrol_project_detail.check_rule,
                    'check_detail_explain': result.check_patrol_project_detail.explain,
                    'check_detail_step': result.check_patrol_project_detail.step,
                })
            else:
                # 环境
                flag = f'ev_{check_patrol_project_id}'
                if not check_dict[check_region_id].get(flag):
                    # 该环境巡检项目的基本信息
                    check_dict[check_region_id][flag] = {
                        'check_id': check_patrol_project_id,
                        'title': result.check_patrol_project.title,
                        'is_equipment': YesOrNo.NO,
                        'check_region_id': check_region_id,
                        'check_patrol_project_id': check_patrol_project_id,
                        'check_patrol_project_detail_id': check_patrol_project_detail_id,
                        'content': []
                    }

                # 具体巡检内容
                check_dict[check_region_id][flag]['content'].append({
                    'result_id': result.id,
                    'value': result.value,
                    'check_detail_type': result.check_patrol_project_detail.type,
                    'check_detail_title': result.check_patrol_project_detail.title,
                    'check_detail_warn_rule': result.check_patrol_project_detail.warn_rule,
                    'check_detail_check_rule': result.check_patrol_project_detail.check_rule,
                    'check_detail_explain': result.check_patrol_project_detail.explain,
                    'check_detail_step': result.check_patrol_project_detail.step
                })

        # 将字典按照区域分开
        for region_id, info in check_dict.items():
            region = region_dict.get(region_id)
            if not region:
                continue
            temp = {
                'region_id': region_id,
                'region_title': region.title,
                'equipment_result': [],
                'environment_result': []
            }
            for check_flag, item_info in info.items():
                if item_info.get('is_equipment') == YesOrNo.YES:
                    temp['equipment_result'].append(item_info)
                else:
                    temp['environment_result'].append(item_info)

            ret_result['check_result'].append(temp)

        return self.report.post(ret_result)

    @request_url(CheckTaskAcceptSchema)
    def check_task_accept(self, form_data):
        """受理巡检任务"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        task_set = CheckTask.query.filter_by(id=form_data['id'], data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        if instance.user_id != None:
            return self.report.error('任务已经被受理，不能再进行受理')

        if g.uid not in instance.user_id_list:
            return self.report.error(f'您不在该任务的巡检任务可受理人员中，不能受理:{g.uid}')

        now_time = datetime.datetime.now()
        now_date = now_time.strftime(current_config.APP_DATE_FORMAT)
        task_start_time_str = instance.task_time_start.strftime(current_config.APP_TIME_FORMAT)
        task_start_time = datetime.datetime.strptime(f'{now_date} {task_start_time_str}',
                                                     current_config.APP_DATETIME_FORMAT)
        if now_time < task_start_time:
            return self.report.error('巡检任务未开始，不能受理')

        # 检查找到受理人所属的班组
        InjectionDataService(form_data).inject_people_group('group_id', 'group_name')
        accept_group_id, accept_group_name = form_data['group_id'], form_data['group_name']
        # 可能受理人和别人调班了，这时候要找到调班人的班组
        exchange_group_id, exchange_group_name = None, None
        # 当前用户正在上的班次
        now_work_type_dict = WorkUtils(data_center_id).get_now_work_type_user()
        now_work_type = now_work_type_dict.get(g.uid)
        if not now_work_type:
            return self.report.error('当前用户找不到正在上班的班次')

        # 找到审批通过的调班申请，找到对应班次，如果找到了，则将调班人的班组置为受理班组
        query_list = [
            WorkExchangeApply.type == ApplyType.Exchange,
            WorkExchangeApply.flow_status == FlowStatus.Done
        ]
        apply_set = WorkExchangeApply.query.filter(
            and_(*query_list, or_(
                WorkExchangeApply.user_name == g.uid,
                WorkExchangeApply.target_user_id == g.uid
            ))
        )
        for apply in apply_set:
            user_id = apply.user_id
            target_user_id = apply.target_user_id
            for detail in apply.detail_set.all():
                # 调班日期、申请人班次id、调班人班次id
                date = detail.date.strftime(current_config.APP_DATE_FORMAT)
                self_work_type_id = detail.self_work_type_id
                target_work_type_id = detail.target_work_type_id
                # 换班日期、申请人换班班次id、调班人换班班次id
                exchange_date = detail.exchange_date.strftime(current_config.APP_DATE_FORMAT)
                self_exchange_work_type_id = detail.self_exchange_work_type_id
                target_exchange_work_type_id = detail.target_exchange_work_type_id

                # 调班日期和换班日期都不是今天，则跳过
                if date != now_date and exchange_date != exchange_date:
                    continue
                if date == now_date:
                    # 判断调班日期是今天
                    if self_work_type_id != now_work_type.id and target_work_type_id != now_work_type.id:
                        continue
                else:
                    # 换班日期是今天
                    if self_exchange_work_type_id != now_work_type.id and target_exchange_work_type_id != now_work_type.id:
                        continue

                # 找到了今天这个班次的调换记录，将对应用户班组设置上
                exchange_user_id = target_user_id if user_id == g.uid else user_id
                group_info = PeopleGroupService.get_user_people_group(data_center_id, exchange_user_id)

                if not group_info:
                    continue
                exchange_group_id = group_info['id']
                exchange_group_name = group_info['name']

        # 得到受理班组信息
        accept_group_id = exchange_group_id if exchange_group_id else accept_group_id
        accept_group_name = exchange_group_name if exchange_group_name else accept_group_name

        try:
            # 设置任务受理人信息
            task_set.update({
                'status': TaskStatus.Executing,
                'start_time': datetime.datetime.now(),
                'group_id': accept_group_id,
                'group_name': accept_group_name,
                'user_id': g.uid,
                'user_name': g.account
            })
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('受理成功')

    @request_url(CheckTaskSuspendSchema)
    def check_task_suspend(self, form_data):
        """巡检任务挂起/恢复"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        task_set = CheckTask.query.filter_by(id=form_data['id'], data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        try:
            task_set.update(form_data)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('巡检任务挂起/恢复成功')

    @request_url(CheckTaskGetRouteInfo)
    def check_task_get_route_info(self, form_data):
        """获取任务的路线信息"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        task_set = CheckTask.query.filter_by(id=form_data['id'], data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        check_route = instance.check_route
        if not check_route:
            return self.report.error('找不到任务对应巡检路线')
        route_detail_set = check_route.route_detail_set.order_by(CheckRouteDetail.index)

        result = []
        for detail in route_detail_set:
            check_region = detail.check_region

            result.append({
                'id': check_region.id,
                'title': check_region.title,
                'index': detail.index,
                'region_code': f'{check_region.data_center_building.code}-{check_region.data_center_floor.code}-{check_region.data_center_room.code}'
            })

        return self.report.post(result)

    @request_url(CheckTaskGetRegionInfo)
    def check_task_get_region_info(self, form_data):
        """获取任务的指定区域信息"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        task_set = CheckTask.query.filter_by(id=form_data['id'], data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        # 找到对应的巡检任务数据，该表在巡检任务生成给时写入，每一条记录，对应每一项检查内容，即【巡检项目的明细】
        result_set = CheckTaskProjectResult.query.filter_by(check_task_id=instance.id,
                                                            check_region_id=form_data['region_id']).all()
        # 先把所有对应设备查出来，存成字典，方便后续取用，不用再多次查询数据库
        equipment_ids = [result.equipment_id for result in result_set if result.equipment_id]
        equipment_set = Equipment.query.filter(Equipment.id.in_(equipment_ids)).all()
        equipment_dict = {equipment.id: equipment for equipment in equipment_set}

        # 字典，key是项目id或者设备id,value是对应的检查内容列表
        check_dict = {}
        for result in result_set:
            check_patrol_project_type = result.check_patrol_project_type
            equipment_id = result.equipment_id
            check_region_id = result.check_region_id
            check_patrol_project_id = result.check_patrol_project_id
            check_patrol_project_detail_id = result.check_patrol_project_detail_id

            if check_patrol_project_type == CheckType.Equipment:
                # 设备
                flag = f'eq_{equipment_id}'
                equipment = equipment_dict.get(equipment_id)
                # 正常不可能找不到设备
                if not equipment:
                    continue
                if not check_dict.get(flag):
                    # 该设备的基本信息
                    check_dict[flag] = {
                        'check_id': equipment.id,
                        'title': result.check_patrol_project.title,
                        'code': equipment.code,
                        'full_code': CodeUtil.get_eq_full_code(equipment),
                        'is_equipment': YesOrNo.YES,
                        'check_region_id': check_region_id,
                        'check_patrol_project_id': check_patrol_project_id,
                        'check_patrol_project_detail_id': check_patrol_project_detail_id,
                        'content': []
                    }

                # 具体巡检内容
                check_dict[flag]['content'].append({
                    'result_id': result.id,
                    'check_detail_type': result.check_patrol_project_detail.type,
                    'check_detail_title': result.check_patrol_project_detail.title,
                    'check_detail_warn_rule': result.check_patrol_project_detail.warn_rule,
                    'check_detail_check_rule': result.check_patrol_project_detail.check_rule,
                    'check_detail_explain': result.check_patrol_project_detail.explain,
                    'check_detail_step': result.check_patrol_project_detail.step
                })
            else:
                # 环境
                flag = f'ev_{check_patrol_project_id}'
                if not check_dict.get(flag):
                    # 该设备的基本信息
                    check_dict[flag] = {
                        'check_id': check_patrol_project_id,
                        'title': result.check_patrol_project.title,
                        'is_equipment': YesOrNo.NO,
                        'check_region_id': check_region_id,
                        'check_patrol_project_id': check_patrol_project_id,
                        'check_patrol_project_detail_id': check_patrol_project_detail_id,
                        'content': []
                    }
                # 具体巡检内容
                check_dict[f'ev_{check_patrol_project_id}']['content'].append({
                    'result_id': result.id,
                    'check_detail_type': result.check_patrol_project_detail.type,
                    'check_detail_title': result.check_patrol_project_detail.title,
                    'check_detail_warn_rule': result.check_patrol_project_detail.warn_rule,
                    'check_detail_check_rule': result.check_patrol_project_detail.check_rule,
                    'check_detail_explain': result.check_patrol_project_detail.explain,
                    'check_detail_step': result.check_patrol_project_detail.step
                })

        return self.report.post(list(check_dict.values()))

    @request_url(CheckTaskPutResult)
    def check_task_put_result(self, form_data):
        """填写巡检内容"""
        id = form_data.get('id')
        region_id = form_data.get('region_id')
        result_content = form_data.get('result_content')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        task_set = CheckTask.query.filter_by(id=id, data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        if instance.status != TaskStatus.Executing:
            return self.report.error('任务不是【执行中】状态，不能填写巡检内容')

        # 首先校验是否全部填写
        result_set = CheckTaskProjectResult.query.filter_by(check_task_id=instance.id, check_region_id=region_id).all()
        need_result_ids = [result.id for result in result_set]
        result_content_dict = {item['id']: item['value'] for item in result_content}
        diff_ids = list(set(need_result_ids) - set(list(result_content_dict.keys())))
        if diff_ids:
            return self.report.error(f'没有填写完整，巡检项填写缺失id列表：{diff_ids}')

        # 接着校验填写内容是否有告警
        warn_list = []
        for result in result_set:
            fill_value = result_content_dict.get(result.id)
            if not fill_value:
                return self.report.error(f'没有填写完整，巡检项填写缺失id列表：{result.id}')
            check_patrol_project_detail = result.check_patrol_project_detail
            # 找不到巡检项目明细
            if not check_patrol_project_detail:
                continue
            # 未开启告警规则
            if check_patrol_project_detail.warn_rule != YesOrNo.YES:
                continue
            check_rule = check_patrol_project_detail.check_rule
            if not check_rule:
                continue

            if check_patrol_project_detail.type == DataType.Number:
                # 数字类型
                fill_value = float(fill_value)
                rule_list = check_rule.get('rule_list')
                if len(rule_list) == 1:
                    symbol = rule_list[0]['symbol']
                    value = float(rule_list[0]['value'])
                    # 判断是否符合告警条件
                    if (symbol == RelationSymbol.Gt and fill_value > value) or \
                            (symbol == RelationSymbol.Lt and fill_value < value) or \
                            (symbol == RelationSymbol.Eq and fill_value == value) or \
                            (symbol == RelationSymbol.Gte and fill_value >= value) or \
                            (symbol == RelationSymbol.Lte and fill_value <= value) or \
                            (symbol == RelationSymbol.Ne and fill_value != value):
                        warn_list.append({
                            'id': result.id,
                            'explain': check_patrol_project_detail.explain,
                            'fill_value': fill_value,
                            'warn_value': f'{fill_value} {RelationSymbol.SYMBOL_NAME.get(symbol)} {value}'
                        })

                else:
                    logic_symbol = check_rule.get('logic_symbol')
                    if logic_symbol == LogicSymbol.And:
                        # 关系运算符【与】
                        symbol_first = rule_list[0]['symbol']
                        value_first = float(rule_list[0]['value'])
                        symbol_last = rule_list[1]['symbol']
                        value_last = float(rule_list[1]['value'])

                        # 检查两者条件都满足
                        if (
                                (symbol_first == RelationSymbol.Gt and fill_value > value_first) or
                                (symbol_first == RelationSymbol.Lt and fill_value < value_first) or
                                (symbol_first == RelationSymbol.Eq and fill_value == value_first) or
                                (symbol_first == RelationSymbol.Gte and fill_value >= value_first) or
                                (symbol_first == RelationSymbol.Lte and fill_value <= value_first) or
                                (symbol_first == RelationSymbol.Ne and fill_value != value_first)
                        ) and (
                                (symbol_last == RelationSymbol.Gt and fill_value > value_last) or
                                (symbol_last == RelationSymbol.Lt and fill_value < value_last) or
                                (symbol_last == RelationSymbol.Eq and fill_value == value_last) or
                                (symbol_last == RelationSymbol.Gte and fill_value >= value_last) or
                                (symbol_last == RelationSymbol.Lte and fill_value <= value_last) or
                                (symbol_last == RelationSymbol.Ne and fill_value != value_last)
                        ):
                            warn_list.append({
                                'id': result.id,
                                'explain': check_patrol_project_detail.explain,
                                'fill_value': fill_value,
                                'warn_value': f'{fill_value} {RelationSymbol.SYMBOL_NAME.get(symbol_first)} {value_first}'
                                              f' {LogicSymbol.EN_NAME.get(logic_symbol)} '
                                              f'{RelationSymbol.SYMBOL_NAME.get(symbol_last)} {value_last}'
                            })

                    else:
                        # 关系运算符【或】
                        symbol_first = rule_list[0]['symbol']
                        value_first = float(rule_list[0]['value'])
                        symbol_last = rule_list[1]['symbol']
                        value_last = float(rule_list[1]['value'])

                        if (
                                (symbol_first == RelationSymbol.Gt and fill_value > value_first) or
                                (symbol_first == RelationSymbol.Lt and fill_value < value_first) or
                                (symbol_first == RelationSymbol.Eq and fill_value == value_first) or
                                (symbol_first == RelationSymbol.Gte and fill_value >= value_first) or
                                (symbol_first == RelationSymbol.Lte and fill_value <= value_first) or
                                (symbol_first == RelationSymbol.Ne and fill_value != value_first)
                        ) or (
                                (symbol_last == RelationSymbol.Gt and fill_value > value_last) or
                                (symbol_last == RelationSymbol.Lt and fill_value < value_last) or
                                (symbol_last == RelationSymbol.Eq and fill_value == value_last) or
                                (symbol_last == RelationSymbol.Gte and fill_value >= value_last) or
                                (symbol_last == RelationSymbol.Lte and fill_value <= value_last) or
                                (symbol_last == RelationSymbol.Ne and fill_value != value_last)
                        ):
                            warn_list.append({
                                'id': result.id,
                                'explain': check_patrol_project_detail.explain,
                                'fill_value': fill_value,
                                'warn_value': f'{fill_value} {RelationSymbol.SYMBOL_NAME.get(symbol_first)} {value_first}'
                                              f' {LogicSymbol.EN_NAME.get(logic_symbol)} '
                                              f'{RelationSymbol.SYMBOL_NAME.get(symbol_last)} {value_last}'
                            })


            elif check_patrol_project_detail.type == DataType.Judge:
                # 判断类型
                now_item = check_rule.get('now_item')
                if now_item == fill_value:
                    warn_list.append({
                        'id': result.id,
                        'explain': check_patrol_project_detail.explain,
                        'fill_value': fill_value,
                        'warn_value': now_item
                    })
            else:
                continue

        # todo 检查事件是否创建，如果没创建，拦截请求，否则，将结果写入到数据库
        has_event = False

        if warn_list and not has_event:
            return self.report.error(f'存在告警，需要先建立事件，告警详情：{warn_list}')

        # todo 将巡检结写入数据表

        return self.report.suc('填写成功')

    @request_url(CheckTaskDone)
    @flow_decorator(FlowServiceWorkExchange)
    def check_task_done(self, form_data):
        """完成巡检任务"""
        id = form_data.get('id')
        summary = form_data.get('summary')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        task_set = CheckTask.query.filter_by(id=id, data_center_id=data_center_id)
        instance = task_set.first()
        if not instance:
            return self.report.error('找不到对应id的巡检任务')

        # 如果本任务下所有巡检结果均已经填写完成，则将状态设置为【已完成】
        not_fill_result = CheckTaskProjectResult.query.filter(
            CheckTaskProjectResult.check_task_id == instance.id,
            CheckTaskProjectResult.value == None
        ).first()

        if not_fill_result:
            return self.report.error(f'还有未填写的巡检项，id：{not_fill_result.id}，不能完成任务')

        # 检查当前时间是否超过巡检时间段的【截至时间】
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        work_end = instance.task_time_end.strftime(current_config.APP_TIME_FORMAT)
        task_end_time = datetime.datetime.strptime(f'{now_date} {work_end}', current_config.APP_DATETIME_FORMAT)
        check_end_time = datetime.datetime.now()

        update_dict = {
            'status': TaskStatus.Done,
            'end_time': check_end_time,
            'summary': summary
        }
        if check_end_time > task_end_time:
            update_dict['is_timeout'] = YesOrNo.YES

        try:
            task_set.update(update_dict)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id

        return self.report.suc('成功完成巡检任务')


check_task_module = CheckTaskModule()
