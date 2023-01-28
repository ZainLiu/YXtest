from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url
from ly_service.utils.Time import timeStampToFormatByDatetime

from models import IsDelete, IsActive
from models.custom_field import CustomFieldValue
from models.equipment import EquipmentType, Equipment
from model_to_view.equipment.schema import EquipmentDeleteSchema, EquipmentActiveSchema, EquipmentUpdateSchema, \
    EquipmentAddSchema, EquipmentQuerySchema
from module.equipment_assets.service.equipment_service import EquipmentService


class EquipmentModule(ModuleBasic):
    """设备相关操作"""

    @request_url(EquipmentQuerySchema)
    def equipment_view(self, req_data):
        equipment_type_id = req_data.get('equipment_type_id')
        id = req_data.get('id')
        name = req_data.get('name')
        code = req_data.get('code')
        supplier_name = req_data.get('supplier_name')
        equipment_model = req_data.get('equipment_model')
        sn_code = req_data.get('sn_code')
        page = req_data.get('page')
        size = req_data.get('size')

        query_list = [Equipment.is_delete == IsDelete.NORMAL, Equipment.equipment_type_id == equipment_type_id]
        if id:
            query_list.append(EquipmentType.id == id)
        if name:
            query_list.append(EquipmentType.name.like(f'%{name}%'))
        if code:
            query_list.append(EquipmentType.code == code)
        if supplier_name:
            query_list.append(EquipmentType.mark.like(f'%{supplier_name}%'))
        if equipment_model:
            query_list.append(EquipmentType.mark.like(f'%{equipment_model}%'))
        if sn_code:
            query_list.append(EquipmentType.mark.like(f'%{sn_code}%'))

        equipment_set = Equipment.query.filter(*query_list)
        count = equipment_set.count()

        try:
            equipment_set = equipment_set.paginate(page, size)
        except:
            equipment_set = equipment_set.paginate(1, size)

        result = []
        for equipment in equipment_set.items:
            # 设备位置
            address = ''
            if equipment.data_center and equipment.data_center_building and equipment.floor and equipment.room:
                address = f'{equipment.data_center.name}-{equipment.data_center_building.building_no}栋-' \
                          f'{equipment.floor.floor_no}楼-{equipment.room.room_no}'
            # 设备位置
            temp = {
                'id': equipment.id,
                'equipment_type_id': equipment.equipment_type_id,
                'name': equipment.name,
                'code': equipment.code,
                'supplier_name': equipment.supplier_name,
                'equipment_model': equipment.equipment_model,
                'produce_time': equipment.produce_time.strftime("%Y-%m-%d %H:%M:%S"),
                'sn_code': equipment.sn_code,
                'is_active': equipment.is_active,
                'custom_fields': [],
                'address': address,
                'data_center': {
                    'id': equipment.data_center.id,
                    'name': equipment.data_center.name
                } if equipment.data_center else None,
                'data_center_building': {
                    'id': equipment.data_center_building.id,
                    'name': equipment.data_center_building.building_no
                } if equipment.data_center_building else None,
                'floor': {
                    'id': equipment.floor.id,
                    'name': equipment.floor.floor_no
                } if equipment.floor else None,
                'room': {
                    'id': equipment.room.id,
                    'name': equipment.room.room_no
                } if equipment.room else None,

            }
            # 自定义字段
            custom_field_set = equipment.equipment_type.custom_field_set
            query_list = [
                CustomFieldValue.field_id.in_([custom_field.id for custom_field in custom_field_set]),
                CustomFieldValue.belong_table_id == equipment.id
            ]
            custom_field_value_dict = {value.field_id: value for value in CustomFieldValue.query.filter(*query_list)}
            for custom_field in custom_field_set:
                custom_field_value = custom_field_value_dict.get(custom_field.id)
                custom_field_temp = {
                    'field_id': custom_field.id,
                    'field_label': custom_field.field_label,
                    'field_name': custom_field.field_name,
                    'field_type': custom_field.field_type,
                    'is_required': custom_field.is_required,
                    'field_value_id': custom_field_value.id if custom_field_value else None,
                    'field_value': custom_field_value.value if custom_field_value else None
                }
                temp['custom_fields'].append(custom_field_temp)

            result.append(temp)

        return self.report.table(result, count)

    @request_url(EquipmentAddSchema)
    def equipment_add(self, req_data):
        custom_field_list = req_data.pop('custom_field_list')
        equipment = Equipment.query.filter_by(code=req_data['code'], is_delete=IsDelete.NORMAL).first()
        if equipment:
            return self.report.error(f"设备编码{req_data['code']}已经存在，不允许再创建本编码的设备")
        try:
            instance = Equipment(**req_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建自定义字段的值[{field_id:1,value:2}...]
            for custom_field_dict in custom_field_list:
                custom_field_dict['belong_table_id'] = instance.id

                custom_field_instance = CustomFieldValue(**custom_field_dict)
                LieYingApp.db.session.add(custom_field_instance)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('创建设备成功')

    @request_url(EquipmentUpdateSchema)
    def equipment_update(self, req_data):
        """更新设备"""
        custom_field_list = req_data.pop('custom_field_list')
        equipment_set = Equipment.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        equipment = equipment_set.first()
        if not equipment:
            return self.report.error('执行更新时找不到对应id的设备')

        try:
            # 如果未激活，则更新设备属性
            if equipment.is_active != IsActive.Active:
                # 先检查要设置的code是否已经存在
                code_equipment = Equipment.query.filter(
                    *[
                        EquipmentType.code == req_data['code'],
                        EquipmentType.id != equipment.id,
                        EquipmentType.is_delete == IsDelete.NORMAL
                    ]
                ).first()
                if code_equipment:
                    return self.report.error(f"该设备编码{req_data['code']}已经存在，不允许再更改为该编码")

                equipment_set.update(req_data)

            # 设备无论是否激活，均可以更新自定义字段的值
            custom_field_set = equipment.equipment_type.custom_field_set
            custom_field_ids = [custom_field.id for custom_field in custom_field_set]
            query_list = [CustomFieldValue.field_id.in_(custom_field_ids),
                          CustomFieldValue.belong_table_id == equipment.id]
            # 如果传递custom_field_list为空数组，则删掉旧的已定义字段值
            if not custom_field_list:
                CustomFieldValue.query.filter(*query_list).delete(synchronize_session=False)
            else:
                for custom_field in custom_field_list:
                    # 这里根据是否有id，如果有id则编辑，没有id则新增
                    if custom_field.get('id'):
                        custom_field_id = custom_field.pop('id')
                        CustomFieldValue.query.filter_by(id=custom_field_id).update(custom_field)
                    else:
                        custom_field['belong_table_id'] = req_data['id']
                        custom_field_instance = CustomFieldValue(**custom_field)
                        LieYingApp.db.session.add(custom_field_instance)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('修改设备成功')

    @request_url(EquipmentActiveSchema)
    def equipment_active(self, req_data):
        """激活设备"""
        equipment_set = Equipment.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        equipment = equipment_set.first()
        if not equipment:
            return self.report.error('找不到对应id的设备')
        if equipment.is_active == req_data['is_active']:
            return self.report.error(f"当前设备状态已经为{IsActive.CN_NAME.get(req_data['is_active'])},不能再进行设置")
        if req_data['is_active'] == IsActive.Disable and equipment.is_active != IsActive.Active:
            return self.report.error(f"当前设备状态为{IsActive.CN_NAME.get(equipment.is_active)},不能进行停用")

        try:
            EquipmentService().change_equipment_status([equipment], active=req_data['is_active'])

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('设备状态更改成功')

    @request_url(EquipmentDeleteSchema)
    def equipment_delete(self, req_data):
        """删除设备"""
        equipment_set = Equipment.query.filter_by(id=req_data['id'], is_delete=IsDelete.NORMAL)
        equipment = equipment_set.first()
        if not equipment:
            return self.report.error('找不到对应id的设备')

        try:
            EquipmentService().change_equipment_status([equipment], delete=IsDelete.Deleted)

            # 提交事务
            LieYingApp.db.session.commit()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('设备删除成功')


equipment_module = EquipmentModule()
