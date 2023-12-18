import abc
from typing import List, Dict, Optional


class ActionHandler(abc.ABC):
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
    def get(self, condition: Optional[Dict] = None) -> List[Action]:
        pass


class ActionJSONHandler(ActionHandler):
    def __init__(self, location: str) -> None:
        """
        :param location: 文件的路径
        """
        import os
        if not os.path.exists(location):
            raise Exception("%s path has no exists" % location)
        self.path = location

    def add(self, data: List[Dict]) -> None:
        """
        :param data: List[Dict] 保存的数据
        """
        try:
            with open(self.path, "r+", encoding="utf-8") as f:
                _data = json.load(f)
                _data.extend(data)
            with open(self.path, "w+", encoding="utf-8") as f:
                json.dump(_data, f, ensure_ascii=False)
        except Exception as e:
            print("save action failed, error: %s" % str(e))

    def delete(self, condition: Dict) -> None:
        """
        :param condition: List[str] 删除的命令
        """
        try:
            with open(self.path, "r+", encoding="utf-8") as f:
                _data = json.load(f)
                _data: List[Dict]
            with open(self.path, "w+", encoding="utf-8") as f:
                result = []
                for idx, item in enumerate(_data):
                    flag = True
                    for k, v in condition.items():
                        if not v or item[k] != v:
                            flag = False
                    if not flag:
                        result.append(item)
                json.dump(result, f, ensure_ascii=False)
        except Exception as e:
            print("delete action failed, error: %s" % str(e))

    def update(self, data: Dict) -> None:
        """
        :param data: List[Dict] 更新的数据
        """
        pass

    def get(self, condition: Optional[Dict] = None) -> List[Action]:
        """
        :param condition: Dict[Str, Any] 筛选条件
        :return: List[Dict]
        """
        result = []
        try:
            with open(self.path, "r+", encoding="utf-8") as f:
                data = json.load(f)
                if not condition:
                    return [Action.to_model(**item) for item in data]
                for item in data:
                    for k, v in condition.items():
                        if not v:
                            continue
                        if item[k] != v:
                            break
                    else:
                        result.append(Action.to_model(**item))
        except Exception as e:
            print("search action by condition failed, error: %s" % str(e))
        return result


action_json = ActionJSONHandler("action.json")
# res = action_json.get({"vendor": "cisco", "model": "nexus"})  # get by conditions
# action_json.add([{ "name": "fans_check", "description": "风扇检查", "vendor": "huawei", "model": "", "cmd": "display fans", "type": "show", "parse_type": "regexp", "parse_content": "" }])
# action_json.delete({"cmd": "display fans", "vendor": "h3c"})
res = action_json.get()
print(res[0])


class ActionORMHandler(ActionHandler):
    def __init__(self, handler):
        # 初始化的时候接收一个handler参数，该参数就是SQLAlchemy的db实例，可以通过这个handler来操作数据库，实现增删改查
        self.handler = handler

    def add(self, args: List[Dict]):
        if self.handler is None:
            raise Exception("has no active db handler")
        actions = []
        for item in args:
            actions.append(Action.to_model(**item))
        self.handler.add_all(actions)
        self.handler.commit()

    def delete(self, args: List[int]):
        if self.handler is None:
            raise Exception("has no active db handler")
        Action.query.filter(Action.id.in_(args)).delete()
        self.handler.commit()

    def update(self, args: List[Dict]):
        if self.handler is None:
            raise Exception("has no active db handler")
        for item in args:
            if "id" not in item:
                continue
            Action.query.filter_by(id=item.pop("id")).update(item)
        self.handler.commit()

    def get(self, filters: Optional[Dict] = None):
        return Action.query.filter_by(**(filters or {})).all()


import abc
import concurrent.futures
import json
import logging
import csv
import traceback
from datetime import datetime
from typing import Any, List, Dict
from flask import Config
from concurrent.futures.thread import ThreadPoolExecutor

from sqlalchemy.orm import scoped_session
from sqlalchemy import and_

from junior.flaskProject.application.services.executor import SSHExecutor
from junior.flaskProject.utils import format_time
from junior.flaskProject.application.models.inspection import Inspection as InspectionModel
from junior.flaskProject.application.services.action import ActionHandler
from junior.flaskProject.application.services.device import DeviceHandler, Device


class InspectionHandler(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def add(self, data: List[Dict]) -> None:
        pass

    @classmethod
    @abc.abstractmethod
    def execute(cls, device: Device, actions: List[Any], config: Dict, action_handler: ActionHandler,
                logger: logging.Logger) -> List[Dict]:
        pass

    @abc.abstractmethod
    def export(self, device_handler: DeviceHandler, start_time: int, end_time: int) -> None:
        pass


class InspectionORMHandler(InspectionHandler):

    def __init__(self, db_handler: scoped_session):
        self.db_handler = db_handler

    def add(self, data: List[Dict]):
        if self.db_handler is None:
            raise Exception("has no active db handler")
        result = []
        for item in data:
            result.append(InspectionModel.to_model(**item))
        self.db_handler.add_all(result)
        self.db_handler.commit()

    @staticmethod
    def check_version(result: List[Dict]) -> List[Dict]:
        pass

    @classmethod
    def execute(cls, device: Device, actions: List[Any], config: Dict, action_handler: ActionHandler,
                logger: logging.Logger) -> List[Dict]:
        result = []
        try:
            with SSHExecutor(
                    username=config.get("SSH_USERNAME"),
                    password=config.get("SSH_PASSWORD"),
                    secret=config.get("SSH_SECRET"),
                    device=device,
                    logger=logger) as ssh:
                for action in actions:
                    ssh.execute(action=action, action_handler=action_handler, parse=True)
                    ssh_result = ssh.result
            for res in ssh_result:
                validation_func = None
                if hasattr(cls, res["action"].name):
                    validation_func = getattr(cls, res["action"].name)
                validation_result = validation_func(res["parse_result"]) if validation_func else res["parse_result"]
                result.append({
                    "action_id": res["action"].id,
                    "output": res["output"],
                    "parse_result": res["parse_result"],
                    "validation_result": validation_result,
                })
        except Exception:
            logger.error(f"execute {device.hostname} failed, err: {traceback.format_exc()}")
        return result

    def export(self, device_handler: DeviceHandler, start_time: datetime, end_time: datetime) -> None:
        data = InspectionModel.query \
            .filter(
            and_(InspectionModel.timestamp > start_time, InspectionModel.timestamp < end_time)) \
            .all()
        device_list = device_handler.get_by_sn([item.sn for item in data])
        sn_map = {item.sn: item for item in device_list}
        header = {"hostname"}
        device_result = {}
        for result in data:
            device = sn_map.get(result.sn)
            if not device:
                continue
            try:
                result_dict = json.loads(result.validation_result)
            except Exception:
                pass
                continue
            for col in result_dict[0].keys():
                header.add(col)
            for row in result_dict:
                device_result.setdefault(device.hostname, {}).update(row)

        with open(f"export_{format_time(0)}.csv", "w+") as f:
            writer = csv.DictWriter(f, fieldnames=list(header))
            writer.writeheader()
            for hostname in device_result:
                writer.writerows([{"hostname": hostname, **device_result[hostname]}])


class InspectionService:
    def __init__(
            self,
            config: Config,
            action_handler: ActionHandler,
            inspection_handler: InspectionHandler,
            logger: logging.Logger,
            max_workers: int = 8) -> None:
        self.config = config
        self.action_handler = action_handler
        self.inspection_handler = inspection_handler
        self.logger = logger
        self.max_workers = max_workers
        self.result: Dict[str, List[Dict]] = {}

    def run(self, device_list: List[Device], actions: List[Any]) -> Dict[str, List[Dict]]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            for device in device_list:
                future: concurrent.futures.Future = pool.submit(
                    self.inspection_handler.execute, device, actions, self.config, self.action_handler, self.logger)
                future.sn = device.sn
                future.add_done_callback(self.execute_callback)
        self.save()
        return self.result

    def execute_callback(self, future: concurrent.futures.Future):
        self.result[future.sn] = future.result()

    def save(self):
        data = []
        for sn, res in self.result.items():
            for content in res:
                for k in content:
                    if isinstance(content[k], list) or isinstance(content[k], dict):
                        content[k] = json.dumps(content[k], ensure_ascii=False)
                data.append({"sn": sn, **content})
        self.inspection_handler.add(data)


@app.cli.command()
def hello():
    click.echo('Hello, Human!')
