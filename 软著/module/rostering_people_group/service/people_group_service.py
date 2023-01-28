from models import IsActive
from models.rostering.people_group import PeopleGroup, PeopleGroupMember


class PeopleGroupService:
    """人员分组相关"""

    @staticmethod
    def get_user_people_group(data_center_id, user_id, attach_member=True):
        """获取用户的人员所属分组信息"""
        member_set = PeopleGroupMember.query.filter(PeopleGroupMember.user_id == user_id).all()
        group = None
        # 找到该用户的所有人员，根据人员找到对应数据中心的分组（正常有且只有一个，有多个时取最后一个）
        for member in member_set:
            group = member.group
            if not group:
                continue
            if group.data_center_id != data_center_id:
                continue
            if group.is_active != IsActive.Active:
                continue
            group = group

        if not group:
            return {}

        result = {
            'id': group.id,
            'name': group.name,
            'type': group.type,
            'leader_id': group.leader_id,
            'leader_name': group.leader_name,
        }

        # 找到该组下的所有成员列表
        if attach_member:
            member_list = []
            for member in group.member_set.all():
                member_list.append({
                    'id': member.id,
                    'user_id': member.user_id,
                    'user_name': member.user_name,
                })
            result['member_list'] = member_list

        return result
