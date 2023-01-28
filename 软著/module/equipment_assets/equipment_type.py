import time

from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url

from models import IsDelete, IsActive
from models.custom_field import CustomField
from models.dictionary import Dictionary
from models.equipment import EquipmentType, EquipmentSubSystem
from model_to_view.equipment_type.schema import EquipmentTypeAddSchema, EquipmentTypeDeleteSchema, \
    EquipmentTypeUpdateSchema, EquipmentTypeActiveSchema, EquipmentTypeQuerySchema
from module.equipment_assets.service.equipment_service import EquipmentService


class EquipmentTypeModule(ModuleBasic):
    """设备类型相关操作"""

    @request_url(EquipmentTypeQuerySchema)
    def equipment_type_view(self, req_data):
        """设备类型列表"""
        sub_system_id = req_data.get('sub_system_id')
        id = req_data.get('id')
        name = req_data.get('name')
        code = req_data.get('code')
        mark = req_data.get('mark')
        page = req_data.get('page')
        size = req_data.get('size')

        query_list = [EquipmentType.is_delete == IsDelete.NORMAL,
                      EquipmentType.equipment_sub_system_id == sub_system_id]
        if id:
            query_list.append(EquipmentType.id == id)
        if name:
            query_list.append(EquipmentType.name.like(f'%{name}%'))
        if code:
            query_list.append(EquipmentType.code == code)
        if mark:
            query_list.append(EquipmentType.mark.like(f'%{mark}%'))

        equipment_type_set = EquipmentType.query.filter(*query_list)
        count = equipment_type_set.count()

        try:
            equipment_type_set = equipment_type_set.paginate(page, size)
        except:
            equipment_type_set = equipment_type_set.paginate(1, size)

        result = []
        for equipment_type in equipment_type_set.items:
            temp = {
                'id': equipment_type.id,
                'equipment_sub_system_id': equipment_type.equipment_sub_system_id,
                'name': equipment_type.name,
                'code': equipment_type.code,
                'mark': equipment_type.mark,
                'is_active': equipment_type.is_active,
                'custom_fields': []
            }
            for custom_field in equipment_type.custom_field_set:
                temp['custom_fields'].append({
                    'id': custom_field.id,
                    'equipment_type_id': custom_field.equipment_type_id,
                    'field_label': custom_field.field_label,
                    'field_name': custom_field.field_name,
                    'field_type': custom_field.field_type,
                    'is_required':custom_field.is_required
                })

            result.append(temp)

        return self.report.table(result, count)

    @request_url(EquipmentTypeAddSchema)
    def equipment_type_add(self, req_data):
        """新增设备类型"""
        custom_field_set = req_data.pop('custom_field_set')
        equipment_type = EquipmentType.query.filter_by(code=req_data['code'], is_delete=IsDelete.NORMAL).first()
        if equipment_type:
            return self.report.error(f"设备类型编码{req_data['code']}已经存在，不允许再创建本编码的设备类型")
        try:
            instance = EquipmentType(**req_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建自定义字段
            for custom_field in custom_field_set:
                custom_field['equipment_type_id'] = instance.id
                custom_field['field_name'] = f'field_{int(time.time())}'

                custom_field_instance = CustomField(**custom_field)
                LieYingApp.db.session.add(custom_field_instance)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('创建设备类型成功')

    @request_url(EquipmentTypeUpdateSchema)
    def equipment_type_update(self, req_data):
        """更新设备类型"""
        custom_field_set = req_data.pop('custom_field_set')
        equipment_type_set = EquipmentType.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        equipment_type = equipment_type_set.first()
        if not equipment_type:
            return self.report.error('执行更新时找不到对应id的设备类型')
        if equipment_type.is_active == IsActive.Active:
            return self.report.error('设备类型已激活，不能再进行编辑')

        code_equipment_type = EquipmentType.query.filter(
            *[
                EquipmentType.code == req_data['code'],
                EquipmentType.id != equipment_type.id,
                EquipmentType.is_delete == IsDelete.NORMAL
            ]
        ).first()
        if code_equipment_type:
            return self.report.error(f"该设备类型编码{req_data['code']}已经存在，不允许再更改为该编码")

        try:
            equipment_type_set.update(req_data)

            # 如果传递custom_field_set为空数组，则删掉旧的已定义字段
            if not custom_field_set:
                ids = [custom_field_obj.id for custom_field_obj in equipment_type.custom_field_set]
                CustomField.query.filter(CustomField.id.in_(ids)).delete(synchronize_session=False)
            else:
                for custom_field in custom_field_set:
                    custom_field_id = custom_field.get('id')
                    # 有id则更新，无id则创建
                    if custom_field_id:
                        custom_field.pop('id')
                        CustomField.query.filter_by(id=custom_field_id).update(custom_field)
                    else:
                        custom_field['equipment_type_id'] = equipment_type.id
                        custom_field['field_name'] = f'field_{int(time.time())}'
                        custom_field_instance = CustomField(**custom_field)
                        LieYingApp.db.session.add(custom_field_instance)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('修改设备类型成功')

    @request_url(EquipmentTypeActiveSchema)
    def equipment_type_active(self, req_data):
        """激活设备类型"""
        equipment_type_set = EquipmentType.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        equipment_type = equipment_type_set.first()
        if not equipment_type:
            return self.report.error('找不到对应id的设备类型')
        if equipment_type.is_active == req_data['is_active']:
            return self.report.error(f"当前设备类型状态已经为{IsActive.CN_NAME.get(req_data['is_active'])},不能再进行设置")
        if req_data['is_active'] == IsActive.Disable and equipment_type.is_active != IsActive.Active:
            return self.report.error(f"当前设备类型状态为{IsActive.CN_NAME.get(equipment_type.is_active)},不能进行停用")

        try:
            EquipmentService().change_equipment_type_status([equipment_type], active=req_data['is_active'])

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('设备设备类型状态更改成功')

    @request_url(EquipmentTypeDeleteSchema)
    def equipment_type_delete(self, req_data):
        """删除设备类型"""
        equipment_type_set = EquipmentType.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        equipment_type = equipment_type_set.first()
        if not equipment_type:
            return self.report.error('找不到对应id的设备类型')

        try:
            EquipmentService().change_equipment_type_status([equipment_type], delete=IsDelete.Deleted)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('设备类型删除成功')


equipment_type_module = EquipmentTypeModule()
