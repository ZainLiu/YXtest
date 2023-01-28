def upload(self):
    file = request.files.get("file")
    df = pd.read_excel(file, sheet_name=None)
    # 校验数据
    company_dict = {}
    country_dict = {}
    province_dict = {}
    data_center_dict = {}
    dcb_dict = {}
    dcf_dict = {}
    dcr_dict = {}
    eq_sys_dict = {}
    eq_sub_sys_dict = {}
    eq_type_dict = {}
    mf_dict = {}
    eq_extra_field_info = self.get_eq_extra_field_info()
    # 处理设备类型
    for index in df.index:
        row = df.loc[index]
        # row = row_raw.values
        # 校验公司名
        company_name = row["公司名称"]
        if not company_dict.get(company_name):
            company = Dictionary.query.filter_by(name=company_name, is_delete=IsDelete.NORMAL).first()
            if not company:
                return self.report.error(f"第{index + 2}行《{company_name}》公司名填写错误或者尚未创建，请去字典模块检查")
            else:
                company_dict[company_name] = company.id
        # 校验国家名
        country_name = row["国家名称"]
        if not country_dict.get(country_name):
            country = Dictionary.query.filter_by(name=company_name, is_delete=IsDelete.NORMAL).first()
            if not country:
                return self.report.error(f"第{index + 2}行《{country_name}》国家名填写错误或者尚未创建，请去字典模块检查")
            else:
                country_dict[country_name] = country.id
        # 校验省份名
        province_name = row["省份名称"]
        if not province_dict.get(province_name):
            province = Dictionary.query.filter_by(name=province_name, is_delete=IsDelete.NORMAL).first()
            if not province:
                return self.report.error(f"第{index + 2}行《{province_name}》省份名填写错误或者尚未创建，请去字典模块检查")
            else:
                province_dict[province_name] = province.id
        # 校验园区名
        data_center_name = row["园区名称"]
        if not data_center_dict.get(data_center_name):
            data_center = DataCenter.query.filter_by(name=data_center_name, is_delete=IsDelete.NORMAL).first()
            if not data_center:
                return self.report.error(f"第{index + 2}行《{data_center_name}》数据中心名填写错误或者尚未创建，请去数据中心模块检查")
            else:
                data_center_dict[data_center_name] = data_center.id
        # 校验楼栋名
        dcb_name = row["栋数名称"]
        if not dcb_dict.get(dcb_name):
            dcb = DataCenterBuilding.query.filter_by(name=dcb_name,
                                                     data_center_id=data_center_dict[data_center_name],
                                                     is_delete=IsDelete.NORMAL).first()
            if not dcb:
                return self.report.error(f"第{index + 2}行《{dcb_name}》数据中心楼栋名填写错误或者尚未创建，请去数据中心模块检查")
            else:
                dcb_dict[dcb_name] = dcb.id
        # 校验楼层名
        dcf_name = row["楼层"]
        if not dcf_dict.get(f"{dcb_name}-{dcf_name}"):
            dcf = DataCenterFloor.query.filter_by(name=dcf_name,
                                                  data_center_building_id=dcb_dict[dcb_name],
                                                  is_delete=IsDelete.NORMAL).first()
            if not dcf:
                return self.report.error(f"第{index + 2}行《{dcf_name}》数据中心楼层名填写错误或者尚未创建，请去数据中心模块检查")
            else:
                dcf_dict[f"{dcb_name}-{dcf_name}"] = dcf.id
        # 校验房间名
        dcr_name = row["房间编号"]
        if not dcr_dict.get(f"{dcb_name}-{dcf_name}-{dcr_name}"):
            result = re.match(r"(.+?)(\d+)", dcr_name)
            dcr = DataCenterRoom.query.filter(DataCenterRoom.code == result.group(2),
                                              DataCenterRoom.room_type.code == result.group(1),
                                              DataCenterRoom.data_center_floor_id == dcf_dict[
                                                  f"{dcb_name}-{dcf_name}"],
                                              DataCenterRoom.is_delete == IsDelete.NORMAL).first()
            if not dcr:
                return self.report.error(f"第{index + 2}行《{dcr_name}》数据中心房间名填写错误或者尚未创建，请去数据中心模块检查")
            else:
                dcr_dict[f"{dcb_name}-{dcf_name}-{dcr_name}"] = dcr.id
        # 校验所属系统
        eq_sys_name = row["所属系统"]
        if not eq_sys_dict.get(eq_sys_name):
            eq_sys = EquipmentSystem.query.filter_by(name=eq_sys_name,
                                                     data_center_id=data_center_dict[data_center_name]).first()
            if not eq_sys:
                return self.report.error(f"第{index + 2}行《{eq_sys_name}》所属系统名填写错误或者尚未创建，请检查无误后再提交")
            else:
                eq_sys_dict[eq_sys_name] = eq_sys.id
        # 校验所属子系统
        eq_sub_sys_name = row["所属子系统"]
        if not eq_sub_sys_dict.get(eq_sub_sys_name):
            eq_sub_sys = EquipmentSubSystem.query.filter_by(name=eq_sub_sys_name,
                                                            equipment_system_id=eq_sys_dict[eq_sys_name],
                                                            is_delete=IsDelete.NORMAL).first()
            if not eq_sub_sys:
                return self.report.error(f"第{index + 2}行《{eq_sys_name}》所属子系统名填写错误或者尚未创建，请检查无误后再提交")
            else:
                eq_sub_sys_dict[eq_sub_sys_name] = eq_sub_sys.id
        # 校验设备类型
        eq_type_name = row["设备类型名称"]
        if not eq_type_dict.get(f"{eq_sub_sys_name}-{eq_type_name}"):
            eq_type = EquipmentType.query.filter_by(name=eq_type_name,
                                                    equipment_sub_system_id=eq_sub_sys_dict[eq_sub_sys_name],
                                                    is_delete=IsDelete.NORMAL).first()
            if not eq_type:
                return self.report.error(f"第{index + 2}行《{eq_type_name}》所属设备类型名填写错误或者尚未创建，请检查无误后再提交")
            else:
                eq_type_dict[f"{eq_sub_sys_name}-{eq_type_name}"] = eq_type.id
        # 校验厂商
        mf_name = row["厂商"]
        if not mf_dict.get(mf_name):
            mf = Manufacturer.query.filter_by(name=mf_name, is_delete=IsDelete.NORMAL).first()
            if not eq_type:
                return self.report.error(f"第{index + 2}行《{mf_name}》厂商名填写错误或者尚未创建，请检查无误后再提交")
            else:
                mf_dict[mf_name] = mf.id
        # 校验额外字段是否合法
        extra_field_info = eq_extra_field_info[eq_type_dict[f"{eq_sub_sys_name}-{eq_type_name}"]]
        for key, val in extra_field_info.items():
            if key not in df.keys():
                return self.report.error(f"第{index + 2}行缺少一个额外字段信息，该字段为:{key}")
            else:
                value = row.get(key)
                if pd.isnull(value) and val["is_required"] == 1:
                    return self.report.error(f"第{index + 2}行缺少一个额外字段的值，此值为必传，该字段为:{key}")
                if val["field_type"] == ExtraFieldType.Number:
                    try:
                        temp_val = float(value)
                    except Exception as e:
                        return self.report.error(f"第{index + 2}行额外字段{key}的值必须为数字，现在的值为{value}")
