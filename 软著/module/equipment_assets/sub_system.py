from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url

from models import IsDelete, IsActive
from models.dictionary import Dictionary
from models.equipment import EquipmentSubSystem, EquipmentType
from model_to_view.sub_system.schema import SubSystemQuerySchema, SubSystemAddSchema, SubSystemUpdateSchema, \
    SubSystemActiveSchema, SubSystemDeleteSchema
from module.equipment_assets.service.equipment_service import EquipmentService


class SubSystemModule(ModuleBasic):
    """设备子系统相关操作"""

    def tree_list(self):
        """获取设备资产树"""
        dictionary = Dictionary.query.filter_by(code='DEVICE', is_delete=IsDelete.NORMAL).first()
        if not dictionary:
            return self.report.error('字典中找不到父类词条：DEVICE')
        system_set = Dictionary.query.filter_by(parent_id=dictionary.id, is_delete=IsDelete.NORMAL)

        result = []
        for system in system_set:
            temp_system = {
                'id': system.id,
                'name': system.name,
                'code': system.code,
                'mark': system.mark,
                'is_delete': system.is_delete,
                'son_list': []
            }
            result.append(temp_system)
            sub_system_set = EquipmentSubSystem.query.filter_by(parent_id=system.id, is_delete=IsDelete.NORMAL)
            for sub_system in sub_system_set:
                temp_sub_system = {
                    'id': sub_system.id,
                    'parent_id': sub_system.parent_id,
                    'name': sub_system.name,
                    'code': sub_system.code,
                    'mark': sub_system.mark,
                    'is_active': sub_system.is_active,
                    'is_delete': system.is_delete,
                    'son_list': []
                }
                temp_system['son_list'].append(temp_sub_system)
                equipment_type_set = EquipmentType.query.filter_by(equipment_sub_system_id=sub_system.id,
                                                                   is_delete=IsDelete.NORMAL)
                for equipment_type in equipment_type_set:
                    temp_equipment_type = {
                        'id': equipment_type.id,
                        'parent_id': equipment_type.equipment_sub_system_id,
                        'name': equipment_type.name,
                        'code': equipment_type.code,
                        'mark': equipment_type.mark,
                        'is_active': equipment_type.is_active,
                        'is_delete': equipment_type.is_delete,
                        'custom_fields': []
                    }

                    for custom_field in equipment_type.custom_field_set:
                        temp_equipment_type['custom_fields'].append({
                            'id': custom_field.id,
                            'equipment_type_id': custom_field.equipment_type_id,
                            'field_label': custom_field.field_label,
                            'field_name': custom_field.field_name,
                            'field_type': custom_field.field_type,
                            'is_required': custom_field.is_required
                        })

                    temp_sub_system['son_list'].append(temp_equipment_type)

        return self.report.post(result)

    @request_url(SubSystemQuerySchema)
    def sub_system_view(self, req_data):
        """获取子系统列表"""
        parent_id = req_data.get('parent_id')
        id = req_data.get('id')
        name = req_data.get('name')
        code = req_data.get('code')
        mark = req_data.get('mark')
        page = req_data.get('page')
        size = req_data.get('size')

        query_list = [EquipmentSubSystem.is_delete == IsDelete.NORMAL, EquipmentSubSystem.parent_id == parent_id]
        if id:
            query_list.append(EquipmentSubSystem.id == id)
        if name:
            query_list.append(EquipmentSubSystem.name.like(f'%{name}%'))
        if code:
            query_list.append(EquipmentSubSystem.code == code)
        if mark:
            query_list.append(EquipmentSubSystem.mark.like(f'%{mark}%'))
        print(query_list)
        sub_system_set = EquipmentSubSystem.query.filter(*query_list)
        count = sub_system_set.count()
        print(sub_system_set.all())
        try:
            sub_system_set = sub_system_set.paginate(page, size)
        except:
            sub_system_set = sub_system_set.paginate(1, size)

        result = []
        for sub_system in sub_system_set.items:
            temp = {
                'id':sub_system.id,
                'parent_id': sub_system.parent_id,
                'name': sub_system.name,
                'code': sub_system.code,
                'mark': sub_system.mark,
                'is_active': sub_system.is_active
            }

            result.append(temp)

        return self.report.table(result, count)

    @request_url(SubSystemAddSchema)
    def sub_system_add(self, req_data):
        """新增设备子系统"""
        sub_system = EquipmentSubSystem.query.filter_by(code=req_data['code'], is_delete=IsDelete.NORMAL).first()
        if sub_system:
            return self.report.error(f"设备子系统编码{req_data['code']}已经存在，不允许再创建本编码的设备子系统")
        try:
            instance = EquipmentSubSystem(**req_data)
            LieYingApp.db.session.add(instance)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('创建设备子系统成功')

    @request_url(SubSystemUpdateSchema)
    def sub_system_update(self, req_data):
        """更新设备子系统"""
        sub_system_set = EquipmentSubSystem.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        sub_system = sub_system_set.first()
        if not sub_system:
            return self.report.error('执行更新时找不到对应id的设备子系统')
        if sub_system.is_active == IsActive.Active:
            return self.report.error('子系统已激活，不能再进行编辑')

        code_sub_system = EquipmentSubSystem.query.filter(
            *[
                EquipmentSubSystem.code == req_data['code'],
                EquipmentSubSystem.id != sub_system.id,
                EquipmentSubSystem.is_delete == IsDelete.NORMAL
            ]
        ).first()
        if code_sub_system:
            return self.report.error(f"该设备子系统编码{req_data['code']}已经存在，不允许再更改为该编码")

        try:
            sub_system_set.update(req_data)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('修改设备子系统成功')

    @request_url(SubSystemActiveSchema)
    def sub_system_active(self, req_data):
        """更改设备子系统激活状态，同时批量更改关联的设备类型、设备"""
        sub_system = EquipmentSubSystem.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL).first()
        if not sub_system:
            return self.report.error('找不到对应id的设备子系统')
        if sub_system.is_active == req_data['is_active']:
            return self.report.error(f"当前子系统状态已经为{IsActive.CN_NAME.get(req_data['is_active'])},不能再进行设置")
        if req_data['is_active'] == IsActive.Disable and sub_system.is_active != IsActive.Active:
            return self.report.error(f"当前子系统状态为{IsActive.CN_NAME.get(sub_system.is_active)},不能进行停用")

        try:
            EquipmentService().change_sub_system_status([sub_system], active=req_data['is_active'])

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('设备子系统更改状态成功')

    @request_url(SubSystemDeleteSchema)
    def sub_system_delete(self, req_data):
        """删除设备子系统，同时批量删除关联的设备类型、设备"""
        sub_system = EquipmentSubSystem.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL).first()
        if not sub_system:
            return self.report.error('找不到对应id的设备子系统')

        try:
            EquipmentService().change_sub_system_status([sub_system], delete=IsDelete.Deleted)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('设备子系统删除成功')


sub_system_module = SubSystemModule()
