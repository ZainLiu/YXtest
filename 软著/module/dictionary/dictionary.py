from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url

from models import IsDelete
from models.dictionary import Dictionary, DictionaryType
from model_to_view.dictionary.deserialize import DictionaryAddDeSerialize, DictionaryUpdateDeSerialize
from model_to_view.dictionary.schema import DictionaryQuerySchema, DictionaryAddSchema, DictionaryUpdateSchema, \
    DictionaryDeleteSchema, DictionaryViewSimpleSchema
from model_to_view.dictionary.serialize import DictionarySerialize
from module.equipment_assets.service.dictionary_service import DictionaryService


class DictionaryModule(ModuleBasic):
    """字典相关操作"""

    @request_url(DictionaryQuerySchema)
    def view(self, req_data):
        """查询字典词条"""
        id = req_data.get('id')
        code = req_data.get('code')
        name = req_data.get('name')
        mark = req_data.get('mark')
        page = req_data.get('page')
        size = req_data.get('size')

        query_list = [Dictionary.is_delete == IsDelete.NORMAL]
        if id:
            query_list.append(Dictionary.id == id)
        if code:
            query_list.append(Dictionary.code == code)
        if name:
            query_list.append(Dictionary.name.like(f'%{name}%'))
        if mark:
            query_list.append(Dictionary.mark.like(f'%{mark}%'))

        # 先通过条件查询所有词条
        query_set = Dictionary.query.filter(*query_list)
        # 接着通过查找到的词条找到所有对应父类词条
        parent_id_list = DictionaryService().get_top_parent_ids(query_set)
        # 最后查找父类词条
        parent_set = Dictionary.query.filter(
            *[
                Dictionary.id.in_(parent_id_list),
                Dictionary.is_delete == IsDelete.NORMAL,
                Dictionary.type == DictionaryType.Parent
            ]
        )
        count = parent_set.count()

        try:
            parent_set = parent_set.paginate(page, size)
        except:
            parent_set = parent_set.paginate(1, size)

        # 这里查的是父类词条，在序列化器内部再查询对应子类
        data = DictionarySerialize().dump(parent_set.items, many=True)

        return self.report.table(data, count)

    @request_url(DictionaryAddSchema)
    def add_parent(self, req_data):
        """新增父类字典词条"""
        if req_data.get('parent_id'):
            del req_data['parent_id']
        req_data['type'] = DictionaryType.Parent
        dictionary = Dictionary.query.filter_by(code=req_data['code'], is_delete=IsDelete.NORMAL,
                                                type=DictionaryType.Parent).first()
        if dictionary:
            return self.report.error(f"字典词条编码{req_data['code']}已经存在，不允许再创建本编码的词条")
        DictionaryAddDeSerialize().load(req_data)
        return self.report.suc('创建字典词条成功')

    @request_url(DictionaryAddSchema)
    def add_son(self, req_data):
        """新增子类字典词条"""
        if not req_data.get('parent_id'):
            return self.report.error('参数缺失：parent_id')
        req_data['type'] = DictionaryType.Son
        dictionary = Dictionary.query.filter_by(code=req_data['code'], is_delete=IsDelete.NORMAL,
                                                parent_id=req_data["parent_id"]).first()
        if dictionary:
            return self.report.error(f"字典词条编码{req_data['code']}在此父类下已经存在，不允许再创建本编码的词条")
        DictionaryAddDeSerialize().load(req_data)
        return self.report.suc('创建字典词条成功')

    @request_url(DictionaryUpdateSchema)
    def update(self, req_data):
        """编辑字典词条"""
        dictionary = Dictionary.query.filter(
            *[
                Dictionary.code == req_data['code'],
                Dictionary.id != req_data['id'],
                Dictionary.is_delete == IsDelete.NORMAL,
            ]
        ).first()
        if dictionary:
            return self.report.error(f"该字典词条编码{req_data['code']}已经存在，不允许再更改为该编码")
        DictionaryUpdateDeSerialize().load(req_data)
        return self.report.suc('修改字典词条成功')

    @request_url(DictionaryDeleteSchema)
    def delete(self, req_data):
        """删除字典词条"""
        dictionary_id = req_data.get('id')
        dictionary = Dictionary.query.filter_by(id=dictionary_id).first()
        if not dictionary:
            return self.report.error('找不到字典词条，请联系管理员')

        try:
            # todo 这里可能后续需要改成：逻辑删除字典词条后，要逻辑删除对应的外键关联表的数据
            dictionary.is_delete = IsDelete.Deleted

            # 按照关系树往下找，所有后代词条均做删除处理
            DictionaryService().delete_children(dictionary.id)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('字典词条删除成功')

    @request_url(DictionaryViewSimpleSchema)
    def view_simple(self, req_data):
        """根据code查找某词条简单的信息"""
        data = Dictionary.query.filter(Dictionary.code == req_data["code"],
                                       Dictionary.is_delete == IsDelete.NORMAL).first()
        if not data:
            return self.report.error("查找不到相关数据")
        data_subs = Dictionary.query.filter(Dictionary.parent_id == data.id,
                                            Dictionary.is_delete == IsDelete.NORMAL).all()
        resp_data = []
        for data_sub in data_subs:
            resp_data.append({
                "id": data_sub.id,
                "code": data_sub.code,
                "name": data_sub.name
            })
        return self.report.post(resp_data)


dictionary_module = DictionaryModule()
