import datetime

from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from models.equipment import EquipmentSystem
from models.event import Event
from models.problem import Problem, Solution
from models.rostering.people_group import PeopleGroup, GroupType
from models.upcoming import Upcoming, UpcomingType
from module.event.serializers.serializer import EventListSerializer
from module.problem.flow_service import FlowServiceProblem, FlowServiceSolution
from module.problem.serializers.schema import *
from module.problem.serializers.serializer import SolutionDetailSerializer, ProblemListSerializer, \
    ProblemDetailSerializer, SolutionListSerializer
from utils.flow_decorator import flow_decorator
from utils.injection_data import set_creator_and_belong_user_info, set_creator_and_belong_user_info_v2
from utils.rpc_func import get_user_current_data_center_id
from utils.serial_number_service import get_serial_number_with_dc_code
from models import db, ProblemSolveStatus, FlowStatus, YesOrNo, SolutionStatus, ProblemStatus, IsActive, IsValid


class ProblemModule(ModuleBasic):
    """问题模块"""

    @request_url(ProblemListSchema)
    def problem_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [Problem.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(Problem.serial_number == form_data["serial_number"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(Problem.equipment_system_id == form_data["eq_sys_id"])
        if form_data.get("level"):
            filter_cond.append(Problem.level == form_data["level"])
        if form_data.get("name"):
            filter_cond.append(Problem.name.like(f"%{form_data['name']}%"))
        p_set = Problem.query.filter(*filter_cond).order_by(Problem.id.desc()).paginate(form_data["page"],
                                                                                        form_data["size"])

        resp_data = ProblemListSerializer(many=True).dump(p_set.items)
        return self.report.table(resp_data, p_set.total)

    @request_url(ProblemDetailSchema)
    def problem_detail(self, form_data):
        problem = Problem.query.filter_by(id=form_data["id"]).first()
        if not problem:
            return self.report.error("相关数据不存在")

        resp_data = ProblemDetailSerializer().dump(problem)
        # 关联事件列表
        event_set = problem.event_set.all()
        event_info = EventListSerializer(many=True).dump(event_set)
        resp_data["event_info"] = event_info
        # 解决方案列表
        solution_set = problem.solution_set.all()
        solution_info = SolutionListSerializer(many=True).dump(solution_set)
        resp_data["solution_info"] = solution_info
        return self.report.post(resp_data)

    def problem_save_or_submit(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        try:
            if form_data.get("id"):
                problem = Problem.query.filter_by(id=form_data["id"]).first()
                if not problem:
                    return self.report.error("相关数据不存在")
            else:
                # 该问题未创建专业组无法生成问题，不然没法处理
                pg = PeopleGroup.query.filter_by(equipment_system_id=form_data["equipment_system_id"],
                                                 type=GroupType.Major,
                                                 is_active=IsActive.Active, data_center_id=dc_id).first()
                if not pg:
                    return self.report.error("该类型还没配置专业组，无法生成问题，因为生成了也没人处理~")
                problem = Problem()
                problem.equipment_system_id = form_data["equipment_system_id"]
                eq_sys = EquipmentSystem.query.filter_by(id=form_data["equipment_system_id"]).first()
                problem.serial_number = get_serial_number_with_dc_code(Problem, f"{eq_sys.code}P", dc_id)
                problem.data_center_id = dc_id
                problem.leader_id = pg.leader_id
                problem.leader_name = pg.leader_name
                set_creator_and_belong_user_info(problem)
            problem.name = form_data.get("name", "")
            problem.level = form_data.get("level", None)
            problem.description = form_data.get("description", "")
            problem.processing_description = form_data.get("processing_description", "")
            problem.affected_area = form_data.get("affected_area", "")
            db.session.add(problem)
            db.session.flush()

            # 绑定事件
            old_event_set = Event.query.filter_by(problem_id=problem.id).all()
            old_event_id_set = set([event.id for event in old_event_set])
            new_event_id_set = set(form_data["event_id_list"])
            will_add_id_list = list(new_event_id_set - old_event_id_set)
            will_delete_id_list = list(old_event_id_set - new_event_id_set)
            # 删除旧的绑定关系
            Event.query.filter(Event.id.in_(will_delete_id_list)).update({"problem_id": None},
                                                                         synchronize_session=False)
            # 绑定新的关系
            Event.query.filter(Event.id.in_(will_add_id_list)).update({"problem_id": problem.id},
                                                                      synchronize_session=False)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"操作失败：{str(e)}")
        db.session.commit()
        g.fid = problem.id
        return self.report.suc("操作成功")

    @request_url(ProblemSaveSchema)
    def problem_save(self, form_data):
        return self.problem_save_or_submit(form_data)

    @request_url(ProblemSubmitSchema)
    @flow_decorator(FlowServiceProblem)
    def problem_submit(self, form_data):
        return self.problem_save_or_submit(form_data)

    @request_url(ProblemAssignSchema)
    def problem_assign(self, form_data):
        """审批通过且未解决的问题才允许指派"""
        try:
            problem = Problem.query.filter_by(id=form_data["id"]).first()
            if not problem:
                return self.report.error("相关数据不存在")
            if problem.leader_id != g.uid:
                return self.report.error("你不是该专业组组长，无法指派")
            if problem.flow_status != FlowStatus.Done:
                return self.report.error("审批未通过的问题无法指派")
            if problem.is_solved in ProblemSolveStatus.CanAccept:
                return self.report.error("解决中和已解决问题不允许重新指派")

            problem.current_acceptor_id = form_data["user_id"]
            problem.current_acceptor_name = form_data["user_name"]
            problem.is_accept = YesOrNo.NO
            problem.is_solved = ProblemSolveStatus.Solving
            db.session.add(problem)
            # 创建一条须解决方案

            solution = Solution()
            solution.serial_number = get_serial_number_with_dc_code(Solution, f"{problem.equipment_system.code}S",
                                                                    problem.data_center_id)
            solution.handler_id = form_data["user_id"]
            solution.handler_name = form_data["user_name"]
            solution.problem_id = problem.id
            set_creator_and_belong_user_info_v2(solution, form_data["user_id"], form_data["user_name"])
            db.session.add(solution)
            db.session.flush()
            # 给指派人增加一条待办去填写方案
            upcoming_obj = Upcoming()
            upcoming_obj.data_center_id = problem.data_center_id
            upcoming_obj.upcoming_type = UpcomingType.FILL_SOLUTION
            upcoming_obj.title = f'填写解决方案-{solution.serial_number}'
            upcoming_obj.form_code = Solution.__name__
            upcoming_obj.form_id = solution.id
            upcoming_obj.user_id = solution.handler_id
            db.session.add(upcoming_obj)
            # 取消指派人的待办
            Upcoming.query.filter(Upcoming.form_id == problem.id, Upcoming.form_code == Problem.__name__,
                                  Upcoming.user_id == problem.leader_id,
                                  Upcoming.title.like(f"%{problem.serial_number}%")).update(
                {"is_valid": IsValid.Deleted}, synchronize_session=False)
        except Exception as e:
            db.session.rollback()
            raise e
            return self.report.error(f"指派失败：{str(e)}")
        db.session.commit()
        return self.report.suc("指派成功")

    @request_url(SolutionAcceptSchema)
    def solution_accept(self, form_data):
        solution = Solution.query.filter_by(id=form_data["id"]).first()
        if not solution:
            return self.report.error("相关数据不存在")
        if solution.handler_id != g.uid:
            return self.report.error("你不是被指派人，不能受理")
        if solution.status != SolutionStatus.NonAccept:
            return self.report.error("非未受理状态下不能受理")
        try:
            solution.status = SolutionStatus.Accepted
            solution.accept_start_time = datetime.datetime.now()
            problem = solution.problem
            problem.status = ProblemStatus.Accepting
            db.session.add(solution)
            db.session.add(problem)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"受理失败{str(e)}")
        db.session.commit()
        return self.report.suc("受理成功")

    @request_url(SolutionFallbackSchema)
    def solution_fallback(self, form_data):
        try:
            solution = Solution.query.filter_by(id=form_data["id"]).first()
            if not solution:
                return self.report.error("相关数据不存在")
            if solution.handler_id != g.uid:
                return self.report.error("你不是被指派人，不能回退")
            if solution.status != SolutionStatus.NonAccept:
                return self.report.error("非未受理状态下不能回退")
            solution.status = SolutionStatus.Fallback
            solution.accept_start_time = datetime.datetime.now()
            solution.fallback_reason = form_data["fallback_reason"]
            db.session.add(solution)
            problem = solution.problem
            problem.status = ProblemStatus.NonAccepted
            db.session.add(problem)
            # 取消当前受理人待办
            Upcoming.query.filter(Upcoming.form_id == solution.id, Upcoming.form_code == Solution.__name__,
                                  Upcoming.user_id == solution.handler_id,
                                  Upcoming.title.like(f"%{solution.serial_number}%")).update(
                {"is_valid": IsValid.Deleted})

            # 给负责人重新生成新的指派待办
            upcoming_obj = Upcoming()
            upcoming_obj.data_center_id = problem.data_center_id
            upcoming_obj.upcoming_type = UpcomingType.PROBLEM_ASSIGN
            upcoming_obj.title = f'指派问题处理-{problem.serial_number}'
            upcoming_obj.form_code = Problem.__name__
            upcoming_obj.form_id = problem.id
            upcoming_obj.user_id = problem.leader_id
            db.session.add(upcoming_obj)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"回退失败：{str(e)}")
        db.session.commit()
        return self.report.suc("回退成功")

    @request_url(SolutionFillSchema)
    @flow_decorator(FlowServiceSolution)
    def solution_fill(self, form_data):
        """填写方案"""
        solution = Solution.query.filter_by(id=form_data["id"]).first()
        if not solution:
            return self.report.error("相关数据不存在")
        if form_data.get("is_change") == YesOrNo.YES and not form_data.get("change_id"):
            return self.report.error("需要变更必须关联相关变更单")
        solution.cause_analysis = form_data["cause_analysis"]
        solution.solution = form_data["solution"]
        solution.annex = form_data["annex"]
        solution.accept_end_time = datetime.datetime.now()
        solution.is_filled = YesOrNo.YES
        db.session.add(solution)
        db.session.commit()
        g.fid = solution.id
        return self.report.suc("填写完毕")

    @request_url(SolutionDetailSchema)
    def solution_detail(self, form_data):
        """解决方案详情"""
        solution = Solution.query.filter_by(id=form_data["id"]).first()
        if not solution:
            return self.report.error("相关数据不存在")

        resp_data = SolutionDetailSerializer().dump(solution)
        event_set = solution.problem.event_set.all()
        event_info = EventListSerializer(many=True).dump(event_set)
        resp_data["problem"]["event_info"] = event_info
        return self.report.post(resp_data)

    @request_url(SolutionSummarySchema)
    def solution_summary(self, form_data):
        """方案总结，是否解决问题"""
        solution = Solution.query.filter_by(id=form_data["id"]).first()
        if not solution:
            return self.report.error("相关数据不存在")
        if solution.flow_status != FlowStatus.Done:
            return self.report.error("审批尚未通过，暂时无法操作")
        problem = solution.problem
        # 如果问题处理人填写问题已解决，则回到组长决定问题是否已解决
        try:
            if form_data.get("is_solved") == YesOrNo.NO:
                solution.status = SolutionStatus.NonSolved

                problem.status = ProblemStatus.NonAccepted
                problem.is_accept = YesOrNo.NO
                problem.is_assign = YesOrNo.NO
                problem.is_follow = YesOrNo.YES
                problem.is_solved = ProblemSolveStatus.NonSolved
                # 给组长生成一条指派待办
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = problem.data_center_id
                upcoming_obj.upcoming_type = UpcomingType.PROBLEM_ASSIGN
                upcoming_obj.title = f'指派问题处理-{problem.serial_number}'
                upcoming_obj.form_code = Problem.__name__
                upcoming_obj.form_id = problem.id
                upcoming_obj.user_id = problem.leader_id
                db.session.add(upcoming_obj)
            else:
                solution.status = SolutionStatus.Solved
                problem.status = ProblemStatus.Completed
                problem.is_solved = YesOrNo.YES
                # 给组长发问题关闭待办
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = problem.data_center_id
                upcoming_obj.upcoming_type = UpcomingType.PROBLEM_CLOSED
                upcoming_obj.title = f'问题完成关闭-{problem.serial_number}'
                upcoming_obj.form_code = Problem.__name__
                upcoming_obj.form_id = problem.id
                upcoming_obj.user_id = problem.leader_id
                db.session.add(upcoming_obj)

            db.session.add(solution)
            db.session.add(problem)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"提交失败，原因：{str(e)}")
        db.session.commit()
        return self.report.suc("提交成功")

    @request_url(ProblemGetMajorPeopleListSchema)
    def get_major_group_people(self, form_data):
        """获取专业组成员，用于指派问题"""
        problem = Problem.query.filter_by(id=form_data["id"]).first()
        if not problem:
            return self.report.error("相关数据不存在")
        pg = PeopleGroup.query.filter_by(data_center_id=problem.data_center_id,
                                         equipment_system_id=problem.equipment_system_id, type=GroupType.Major,
                                         is_active=IsActive.Active).first()
        member_set = pg.member_set.filter_by(is_leader=YesOrNo.NO).all()
        resp_data = []
        for member in member_set:
            resp_data.append({
                "id": member.user_id,
                "name": member.user_name
            })
        return self.report.post(resp_data)


problem_module = ProblemModule()
