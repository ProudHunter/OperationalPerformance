from app.utils import to_model, to_dict


class Action(db.Model):
    __tablename__ = "action"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False, comment="动作名称")
    description = db.Column(db.String(256), comment="动作描述")
    vendor = db.Column(db.String(64), comment="厂商")
    model = db.Column(db.String(64), comment="型号")
    cmd = db.Column(db.String(256), nullable=False, comment="命令行")
    type = db.Column(db.String(8), comment="命令类型[show|config]")
    parse_type = db.Column(db.String(8), comment="解析类型[regexp|textfsm]")
    parse_content = db.Column(db.String(1024), comment="解析内容")

    @classmethod
    def to_model(cls, **kwargs) -> Dict:
        return to_model(cls, **kwargs)

    def to_dict(self) -> db.Model:
        return to_dict(self)


class Devices(db.Model):
    __tablename__ = "devices"
    sn = db.Column(db.String(128), primary_key=True, comment="资产号")
    ip = db.Column(db.String(16), nullable=False, comment="IP地址")
    hostname = db.Column(db.String(128), nullable=False, comment="主机名")
    idc = db.Column(db.String(32), comment="机房")
    vendor = db.Column(db.String(16), comment="厂商")
    model = db.Column(db.String(16), comment="型号")
    role = db.Column(db.String(8), comment="角色")
    created_at = db.Column(db.DateTime(), nullable=False, server_default=text('NOW()'), comment="创建时间")
    updated_at = db.Column(db.DateTime(), nullable=False, server_default=text('NOW()'), server_onupdate=text('NOW()'),
                           comment="修改时间")

    detail = db.relationship("DeviceDetail", uselist=False, backref="device")
    ports = db.relationship("Ports", uselist=True, backref="device")

    @classmethod
    def to_model(cls, **kwargs):
        return to_model(**kwargs)

    def to_dict(self):
        res = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(col.type, DateTime):  # 判断类型是否为DateTime
                if not val:  # 判断实例中该字段是否有值
                    value = ""
                else:  # 进行格式转换
                    value = val.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(col.type, Numeric):  # 判断类型是否为Numeric
                value = float(val)  # 进行格式转换
            else:  # 剩余的直接取值
                value = val
            res[col.name] = value
        return res
