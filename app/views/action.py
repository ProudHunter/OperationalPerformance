from flask import Blueprint, request, current_app
from ..models import db
from app.services import ActionORMHandler

action_blueprint = Blueprint("action", __name__, url_prefix="/action")


@action_blueprint.route("/add", methods=["POST"])
def add():
    data = request.get_json()
    try:
        ActionORMHandler(db.session()).add(data)
        current_app.logger.success("add success")
        return "success"
    except Exception as e:
        raise DBError(message=str(e))




@action_blueprint.route("delete", methods=["POST"])
def delete():
    data = request.get_json()
    ActionORMHandler(db.session()).delete(data)
    return "success"


@action_blueprint.route("update", methods=["POST"])
def update():
    data = request.get_json()
    ActionORMHandler(db.session()).update(data)
    return "success"


@action_blueprint.route("/get")
def get():
    args = request.args.to_dict()
    res = ActionORMHandler(db.session()).get(args)
    return [item.to_dict() for item in res]
