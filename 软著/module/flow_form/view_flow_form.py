from flask import g, current_app
from ly_kernel.LieYing import LieYingApp
from ly_kernel.Module import ModuleBasic, request_url
from model_to_view.flow_form.deserialize import FlowFormDeserialize
from model_to_view.flow_form.schema import FlowFormDeleteSchema, FlowFormPutSchema
from model_to_view.flow_form.serializer import FlowFormListSerialize
from models.flow_form import FlowForm, FlowFormScene


class FlowFormModule(ModuleBasic):
    """审批表单管理"""

    def list(self):
        """审批场景列表"""
        form_set = FlowForm.query.order_by(FlowForm.form_name)
        count = form_set.count()
        data = FlowFormListSerialize(many=True).dump(form_set)

        return self.report.table(*(data, count))

    @request_url(FlowFormPutSchema)
    def update(self, req_data):
        """修改审批表单"""
        form_id = req_data.get('id')
        form = FlowForm.query.filter_by(id=form_id).first()
        if not form:
            return self.report.error('找不到审批表单，请联系管理员')

        FlowFormDeserialize().load(req_data)

        return self.report.suc('审批表单修改成功')

    @request_url(FlowFormDeleteSchema)
    def delete(self, req_data):
        """删除审批表单"""
        form_id = req_data.get('id')
        form = FlowForm.query.filter_by(id=form_id).first()
        if not form:
            return self.report.error('找不到审批表单，请联系管理员')

        try:
            # 删除表单场景
            FlowFormScene.query.filter_by(flow_form_id=form_id).delete()
            # 删除表单
            FlowForm.query.filter_by(id=form_id).delete()

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('审批表单删除成功')


form_module = FlowFormModule()
