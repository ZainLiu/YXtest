from ly_kernel.Module import ModuleBasic, request_url
from sqlalchemy import or_

from models import IsDelete, db, IsActive
from models.dictionary import Dictionary
from models.space import Space
from model_to_view.space.schema import SpaceAddSchema, SpaceUpdateSchema, SpaceDeleteSchema, SpaceActiveSchema, \
    SpaceViewSchema, SpaceViewSimpleSchema


class SpaceModule(ModuleBasic):

    @request_url(SpaceAddSchema)
    def add(self, form_data):
        space_area = Dictionary.query.filter(Dictionary.id == form_data["space_area_id"]).first()
        if not space_area:
            return self.report.error("空间区域不存在")
        code = form_data["code"]
        old_space = Space.query.filter(or_(Space.code == code, Space.name == form_data["name"]),
                                       Space.is_delete == IsDelete.NORMAL).first()
        if old_space:
            return self.report.error("名字或编码重复，请重修修改后再录入")
        space = Space()
        space.name = form_data["name"]
        space.code = form_data["code"]
        space.mark = form_data["mark"]
        space.space_area_id = space_area.id
        db.session.add(space)
        db.session.commit()
        return self.report.suc("新增空间成功")

    @request_url(SpaceUpdateSchema)
    def update(self, form_data):
        space = Space.query.filter(Space.id == form_data["id"]).first()
        if not space:
            return self.report.error("查找不到相关的空间数据")
        if space.is_active != IsActive.NonActive:
            return self.report.error("仅非激活状态允许编辑~")
        if space.code != form_data["code"] or space.name != form_data["name"]:
            old_space = Space.query.filter(or_(Space.code == form_data["code"], Space.name == form_data["name"]),
                                           Space.is_delete == IsDelete.NORMAL).first()
            if old_space:
                return self.report.error("空间名或编码重复，请重新修改后再录入")
        space.name = form_data["name"]
        space.code = form_data["code"]
        space.mark = form_data["mark"]
        db.session.add(space)
        db.session.commit()
        return self.report.suc("空间更新成功")

    @request_url(SpaceDeleteSchema)
    def delete(self, form_data):
        space = Space.query.filter(Space.id == form_data["id"]).first()
        if not space:
            return self.report.error("查找不到相关的空间数据")
        if space.is_active == IsActive.Active:
            return self.report.error("已激活过的空间不允许删除")
        space.is_delete = IsDelete.Deleted
        db.session.add(space)
        db.session.commit()
        return self.report.suc("空间删除成功")

    @request_url(SpaceActiveSchema)
    def active(self, form_data):
        space = Space.query.filter(Space.id == form_data["id"]).first()
        if not space:
            return self.report.error("查找不到相关的空间数据")
        is_active = form_data['is_active']
        if is_active not in [IsActive.Active, IsActive.Disable]:
            return self.report.error("状态参数is_active非法")
        space.is_active = is_active
        db.session.add(space)
        db.session.commit()
        return self.report.suc(f"{IsActive.CN_NAME[is_active]}成功~")

    @request_url(SpaceViewSchema)
    def view(self, form_data):
        space_area = Dictionary.query.filter(Dictionary.id == form_data["space_area_id"]).first()
        if not space_area:
            return self.report.error("空间区域不存在")
        filter_cond = [Space.is_delete == IsDelete.NORMAL, Space.space_area_id == space_area.id]
        if form_data["name"]:
            filter_cond.append(Space.name.like(f"%{form_data['name']}%"))
        if form_data["code"]:
            filter_cond.append(Space.name.like(f"%{form_data['code']}%"))
        if form_data["is_active"] in [IsActive.Active, IsActive.NonActive, IsActive.Disable]:
            filter_cond.append(Space.is_active == form_data["is_active"])
        page_data = Space.query.filter(*filter_cond).order_by(Space.id.desc()).paginate(form_data["page"],
                                                                                        form_data["size"])
        resp_data = []
        for item in page_data.items:
            resp_data.append({
                "id": item.id,
                "name": item.name,
                "code": item.code,
                "mark": item.mark,
                "is_active": item.is_active
            })
        return self.report.table(resp_data, page_data.total)

    @request_url(SpaceViewSimpleSchema)
    def view_simple(self, form_data):
        filter_cond = [Space.is_delete == IsDelete.NORMAL, Space.is_active == IsActive.Active]
        if form_data["name"]:
            filter_cond.append(Space.name.like(f"%{form_data['name']}%"))
        if form_data["space_area_id"]:
            filter_cond.append(Space.space_area_id == form_data["space_area_id"])
        spaces = Space.query.filter(*filter_cond).all()
        resp_data = []
        for space in spaces:
            resp_data.append({
                "id": space.id,
                "name": space.name
            })
        return self.report.post(resp_data)


spec_module = SpaceModule()
