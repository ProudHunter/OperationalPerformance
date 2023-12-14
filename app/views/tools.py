from flask import Blueprint, jsonify

from hobbit_core.pagination import PageParams, pagination  # NOQA

from app.services import OptionService

bp = Blueprint('tools', __name__)


@bp.route('/ping', methods=['GET'])
def ping():
    """ For health check.
    """
    return jsonify({'ping': 'ok'})


@bp.route('/options', methods=['GET'])
def option():
    """ List all enums for frontend.
    """
    return jsonify(OptionService.get_options())
