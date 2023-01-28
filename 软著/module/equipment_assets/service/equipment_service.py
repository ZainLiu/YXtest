from ly_kernel.LieYing import LieYingApp


class EquipmentService():

    def change_sub_system_status(self, sub_system_set, active=None, delete=None):
        """改变子系统的状态（激活、删除）,"""
        assert active or delete, 'active或者delete参数必须至少传递一个'
        for sub_system in sub_system_set:
            if active:
                sub_system.is_active = active
            if delete:
                sub_system.is_delete = delete

            self.change_equipment_type_status(sub_system.equipment_type_set, active, delete)

    def change_equipment_type_status(self, equipment_type_set, active=None, delete=None):
        """改变设备类型的状态（激活、删除）"""
        assert active or delete, 'active或者delete参数必须至少传递一个'
        for equipment_type in equipment_type_set:
            if active:
                equipment_type.is_active = active
            if delete:
                equipment_type.is_delete = delete

            self.change_equipment_type_status(equipment_type.equipment_set, active, delete)

    def change_equipment_status(self, equipment_set, active=None, delete=None):
        """改变设备的状态（激活、删除）"""
        assert active or delete, 'active或者delete参数必须至少传递一个'

        for equipment in equipment_set:
            if active:
                equipment.is_active = active
            if delete:
                equipment.is_delete = delete
