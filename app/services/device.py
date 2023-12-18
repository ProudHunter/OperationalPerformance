import abc
from typing import List, Dict, Optional


class DeviceHandler(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def add(self, data: List[Dict]) -> None:
        pass

    @abc.abstractmethod
    def delete(self, data: Dict) -> None:
        pass

    @abc.abstractmethod
    def update(self, data: Dict) -> None:
        pass

    @abc.abstractmethod
    def get(self, condition: Optional[Dict] = None) -> List[Device]:
        pass


class DeviceDBHandler(DeviceHandler):
    def __init__(self, user: str, password: str, host: str, database: str, port: int = 3306) -> None:
        self.conn = pymysql.connect(user=user, password=password, host=host, port=port, database=database,
                                    cursorclass=DictCursor)
        self.conn: pymysql.connections.Connection

    def get_conn(self) -> Cursor:
        if self.conn is None:
            raise Exception("mysql is lost connection")
        return self.conn.cursor()

    def close_db(self):
        self.conn.close()

    def add(self, data: List[Dict]) -> None:
        cursor = self.get_conn()
        device_sql = "insert into devices (sn, ip, hostname, idc, vendor, model, role) values (%s, %s, %s, %s, %s, %s, %s);"
        device_detail_sql = "insert into device_detail values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        device_data = []
        device_detail_data = []
        for item in data:
            device_data.append([
                item.get("sn", ""), item.get("ip", ""), item.get("hostname", ""), item.get("idc", ""),
                item.get("vendor", ""), item.get("model", ""), item.get("role", "")
            ])
            device_detail_data.append([
                item.get("sn", ""), item.get("ipv6", ""), item.get("console_ip", ""), item.get("row", ""),
                item.get("column", ""), item.get("last_start", ""), item.get("runtime", ""),
                item.get("image_version", ""),
                item.get("over_warrant"), item.get("warrant_time")
            ])
        try:
            cursor.executemany(device_sql, device_data)
            cursor.executemany(device_detail_sql, device_detail_data)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception("db insert failed, error: %s" % str(e))
        finally:
            cursor.close()

    def delete(self, data: Dict) -> None:
        pass

    def update(self, data: Dict) -> None:
        pass

    def get(self, condition: Optional[Dict] = None) -> List[Device]:
        cursor = self.get_conn()
        sql = "select ip, hostname, vendor, model, hardware, channel, device_type from devices " \
              "join device_detail on devices.sn = device_detail.sn"
        where_str = []
        if condition is not None:
            for k, v in condition.items():
                if isinstance(v, int):
                    where_str.append("%s=%d" % (k, v))
                else:
                    where_str.append("%s='%s'" % (k, v))
        if len(where_str) > 0:
            sql += (" where %s" % ",".join(where_str))
        cursor.execute(sql)
        result = cursor.fetchall()
        devices = []
        for item in result:
            devices.append(Device().to_model(**item))
        return devices
