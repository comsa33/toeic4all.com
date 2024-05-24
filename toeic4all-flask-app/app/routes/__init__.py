from flask import Blueprint, render_template, send_from_directory, request
from flask import current_app as app
from datetime import datetime


main_bp = Blueprint('main', __name__)


@main_bp.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}


@main_bp.route('/')
def main_page():
    return render_template('main_page.html')


@main_bp.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@main_bp.route('/sitemap.xml')
def serve_sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')


@main_bp.route('/part5/test')
def mock_test():
    return render_template('mock_test.html')


@main_bp.route('/board')
def board_page():
    return render_template('board.html')


@main_bp.route('/user-detail')
def user_detail():
    return render_template('user_detail.html')


@main_bp.route('/mypage')
def my_page():
    return render_template('my_page.html')


@main_bp.route('/mynote')
def my_note():
    return render_template('my_note.html')


@main_bp.route('/my-learning-analysis')
def my_learning_analysis():
    return render_template('my_learning_analysis.html')


@main_bp.route('/rank')
def rank():
    return render_template('rank.html')


@main_bp.route('/voca-test')
def voca_test():
    return render_template('voca_test.html')


@main_bp.route('/myvoca')
def my_voca():
    return render_template('my_voca.html')
