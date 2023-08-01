from ly_kernel.db.BaseModel import *


class FlowTpl(BaseModel):
    """
    模板
    """
    __tablename__ = 'wf_tpl'

    id = db.Column(db.Integer, primary_key=True)
    os = db.Column(db.Integer, default="", comment='系统类型')
    title = db.Column(db.String(100), default="", comment='标题')
    order_tpl_id = db.Column(db.Integer, default=0, comment='工单模板ID')
    tpl_data = db.Column(db.JSON, nullable=False, comment='模板')
    specs_data = db.Column(db.JSON, nullable=True, comment='规则')
    createTime = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'), comment='创建时间')
    updateTime = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'),
                           server_onupdate=db.text('CURRENT_TIMESTAMP'), comment='更新时间')

