from flask import Blueprint, jsonify
from sqlalchemy.orm.exc import NoResultFound

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def handle_404(e):
    return jsonify(error=str(e)), 404


@errors.app_errorhandler(500)
def handle_500(e):
    return jsonify(error=str(e)), 500


@errors.app_errorhandler(NoResultFound)
def handle_no_result_exception(e):
    return jsonify(error="Resource not found"), 404
