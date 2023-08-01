from ly_kernel.Module import ModuleBasic, request_url
from serializers.FlowTplSchema import FlowTplViewSchema, FlowTplViewModelSchema, FlowTplFormSchema
import module.flowTpl.FlowTplService as flowtplService
from models.FlowTpl import FlowTpl
from module.flowTpl.FlowToSpecs import FlowToSpecs


# 事件模块
class FlowTplModule(ModuleBasic):

    @request_url(FlowTplViewSchema)
    def view(self, req_data):
        flow_tpl, total = flowtplService.get_flow_tpl_list(req_data)

        data = FlowTplViewModelSchema(many=True).dump(flow_tpl)

        return self.report.table(data, total)

    @request_url(FlowTplFormSchema)
    def add(self, form_data):
        flow_tpl = FlowTpl()
        flow_tpl.os = form_data.get("os")
        flow_tpl.title = form_data.get("title")
        flow_tpl.order_tpl_id = form_data.get("order_tpl_id")
        flow_tpl.tpl_data = form_data.get("tpl_data")
        flow_tpl.specs_data = FlowToSpecs().loads(flow_tpl.tpl_data).to_json()

        flow_tpl.add()

        return self.report.status()

    @request_url(FlowTplFormSchema)
    def edit(self, form_data):
        flow_tpl_id = form_data.get("id")
        db_flow_tpl = flowtplService.get_flow_tpl_by_id(flow_tpl_id)
        if db_flow_tpl is None:
            return self.report.error("模板不存在")

        tpl_data = form_data.get("tpl_data")

        FlowTpl.query.filter(FlowTpl.id == flow_tpl_id).update(
            {
                "title": form_data.get("title"), "tpl_data": tpl_data,
                "order_tpl_id": form_data.get("order_tpl_id", 0),
                "specs_data": FlowToSpecs().loads(tpl_data).to_json()
            }
        )

        FlowTpl.dbcommit()

        return self.report.status()

    def delete(self):
        r_data = self.getAllRequestData().get("ids", '')

        FlowTpl.query.filter(FlowTpl.id.in_(r_data)).delete(
            synchronize_session=False
        )

        FlowTpl.dbcommit()
        return self.report.status()


flowtpl_module = FlowTplModule()
