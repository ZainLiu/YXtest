from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.room_type.schema import *
from models import IsDelete, db, YesOrNo
from models.data_center import RoomType


class RoomTypeModule(ModuleBasic):
    @request_url(RoomTypeCreateSchema)
    def rt_create(self, form_data):
        old_record_name = RoomType.query.filter_by(is_delete=IsDelete.NORMAL, name=form_data["name"]).first()
        if old_record_name:
            return self.report.error("已有相同名字的类型")

        old_record_code = RoomType.query.filter_by(is_delete=IsDelete.NORMAL, name=form_data["code"]).first()
        if old_record_code:
            return self.report.error("已有相同房间编码")

        rt = RoomType()
        rt.name = form_data["name"]
        rt.code = form_data["code"]
        rt.introduction = form_data["introduction"]
        rt.creator_id = g.uid
        rt.creator_name = g.account
        db.session.add(rt)
        db.session.commit()
        return self.report.suc("新增成功")

    @request_url(RoomTypeUpdateSchema)
    def rt_update(self, form_data):
        rt = RoomType.query.filter_by(id=form_data["id"]).first()
        if not rt:
            return self.report.error("房间类型不存在")
        if rt.code != form_data["code"]:
            old_record_code = RoomType.query.filter_by(is_delete=IsDelete.NORMAL, name=form_data["code"]).first()
            if old_record_code:
                return self.report.error("已有相同房间编码")

        rt.code = form_data["code"]
        rt.introduction = form_data["introduction"]
        db.session.add(rt)
        db.session.commit()
        return self.report.suc("修改成功")

    @staticmethod
    def rt_status_switch(rt, status):
        rt.is_active = status
        db.session.add(rt)
        db.session.commit()

    @request_url(RoomTypeStatusSwitchSchema)
    def rt_active(self, form_data):
        rt = RoomType.query.filter_by(id=form_data["id"]).first()
        if not rt:
            return self.report.error("房间类型不存在")
        self.rt_status_switch(rt, YesOrNo.YES)
        return self.report.suc("激活成功")

    @request_url(RoomTypeStatusSwitchSchema)
    def rt_disable(self, form_data):
        rt = RoomType.query.filter_by(id=form_data["id"]).first()
        if not rt:
            return self.report.error("房间类型不存在")
        self.rt_status_switch(rt, YesOrNo.NO)
        return self.report.suc("停用成功")

    # @request_url(RoomTypeListSchema)
    def rt_list(self):
        rt_set = RoomType.query.filter_by(is_delete=IsDelete.NORMAL).all()
        resp_data = []
        for rt in rt_set:
            resp_data.append({
                "id": rt.id,
                "name": rt.name,
                "code": rt.code,
                "introduction": rt.introduction,
                "is_active": rt.is_active,
                "is_sys_conf": rt.is_sys_conf
            })
        return self.report.post(resp_data)

    # @request_url(RoomTypeListSchema)
    def rt_list_simple(self):
        rt_set = RoomType.query.filter_by(is_delete=IsDelete.NORMAL, is_active=YesOrNo.YES).all()
        resp_data = []
        for rt in rt_set:
            resp_data.append({
                "id": rt.id,
                "name": rt.name,
                "code": rt.code
            })
        return self.report.post(resp_data)


rt_module = RoomTypeModule()
