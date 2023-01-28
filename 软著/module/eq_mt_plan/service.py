from models import EquipmentStatus, db, MaintenanceCycle
from models.equipment import Equipment
from models.maintenance_task import EquipmentMaintenanceTask, EquipmentMaintenanceSubTask
from models.upcoming import Upcoming, UpcomingType
from utils.serial_number_service import get_serial_number_with_dc_code_by_redis


def generate_eq_maintenance_task(emp):
    """生成设备型号维保任务"""
    empd_set = emp.empd_set.all()
    for empd in empd_set:
        if empd.period == MaintenanceCycle.Monthly:
            fill_data = empd.emi.monthly_template
        elif empd.period == MaintenanceCycle.Quarterly:
            fill_data = empd.emi.quarterly_template
        elif empd.period == MaintenanceCycle.SemiAnnually:
            fill_data = empd.emi.semiannually_template
        elif empd.period == MaintenanceCycle.Annually:
            fill_data = empd.emi.annually_template
        else:
            fill_data = {}
        emt = EquipmentMaintenanceTask()
        emt.serial_number = get_serial_number_with_dc_code_by_redis("WBRWS", emp.data_center_id)
        emt.data_center_id = emp.data_center_id
        emt.leader_id = emp.leader_id
        emt.leader_name = emp.leader_name
        emt.empd_id = empd.id
        emt.creator_id = emp.leader_id
        emt.creator_name = emp.leader_name
        emt.belong_user_id = emp.leader_id
        emt.belong_user_name = emp.leader_name
        db.session.add(emt)
        db.session.flush()
        # 创建待办,让负责人分配任务
        upcoming_obj = Upcoming()
        upcoming_obj.data_center_id = emt.data_center_id
        upcoming_obj.upcoming_type = UpcomingType.ASSIGN_MT_SUB_TASK
        upcoming_obj.title = f'分配维保子任务-{emt.serial_number}'
        upcoming_obj.form_code = EquipmentMaintenanceTask.__name__
        upcoming_obj.form_id = emt.id
        upcoming_obj.user_id = emt.leader_id
        db.session.add(upcoming_obj)

        eq_set = Equipment.query.filter_by(data_center_id=emp.data_center_id,
                                           equipment_model=empd.emi.equipment_model,
                                           status=EquipmentStatus.Using).all()

        for eq in eq_set:
            emst = EquipmentMaintenanceSubTask()
            emst.serial_number = get_serial_number_with_dc_code_by_redis("WBZRWS", emp.data_center_id)
            emst.equipment_id = eq.id
            emst.data_center_id = emp.data_center_id
            emst.emt_id = emt.id
            emst.fill_data = fill_data
            db.session.add(emst)
