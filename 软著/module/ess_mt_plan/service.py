from models import db, MaintenanceCycle
from models.maintenance_task import EquipmentSubSystemMaintenanceTask, EquipmentSubSystemMaintenanceSubTask
from models.upcoming import Upcoming, UpcomingType
from utils.serial_number_service import get_serial_number_with_dc_code_by_redis


def generate_ess_maintenance_task(essmp):
    """生成设备型号维保任务"""
    essmpd_set = essmp.essmpd_set.all()
    for essmpd in essmpd_set:
        if essmpd.period == MaintenanceCycle.Monthly:
            fill_data = essmpd.essmi.monthly_template
        elif essmpd.period == MaintenanceCycle.Quarterly:
            fill_data = essmpd.essmi.quarterly_template
        elif essmpd.period == MaintenanceCycle.SemiAnnually:
            fill_data = essmpd.essmi.semiannually_template
        elif essmpd.period == MaintenanceCycle.Annually:
            fill_data = essmpd.emi.annually_template
        else:
            fill_data = {}
        essmt = EquipmentSubSystemMaintenanceTask()
        essmt.serial_number = get_serial_number_with_dc_code_by_redis("WBRWS", essmp.data_center_id)
        essmt.data_center_id = essmp.data_center_id
        essmt.leader_id = essmp.leader_id
        essmt.leader_name = essmp.leader_name
        essmt.essmpd_id = essmpd.id
        essmt.creator_id = essmp.leader_id
        essmt.creator_name = essmp.leader_name
        essmt.belong_user_id = essmp.leader_id
        essmt.belong_user_name = essmp.leader_name
        db.session.add(essmt)
        db.session.flush()
        # 创建待办,让负责人分配任务
        upcoming_obj = Upcoming()
        upcoming_obj.data_center_id = essmt.data_center_id
        upcoming_obj.upcoming_type = UpcomingType.ASSIGN_MT_SUB_TASK
        upcoming_obj.title = f'分配设备子系统维保子任务-{essmt.serial_number}'
        upcoming_obj.form_code = EquipmentSubSystemMaintenanceTask.__name__
        upcoming_obj.form_id = essmt.id
        upcoming_obj.user_id = essmt.leader_id
        db.session.add(upcoming_obj)

        batch_set = essmpd.essmi.essmib_set.all()

        for batch in batch_set:
            essmst = EquipmentSubSystemMaintenanceSubTask()
            essmst.serial_number = get_serial_number_with_dc_code_by_redis("WBZRWS", essmp.data_center_id)
            essmst.essmib_id = batch.id
            essmst.data_center_id = essmp.data_center_id
            essmst.essmt_id = essmt.id
            essmst.fill_data = fill_data
            db.session.add(essmst)
