from flask import Flask, jsonify
from flask_cors import CORS
from api.routes import api_bp
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 注册蓝图
    register_blueprints(app)

    # 配置日志
    configure_logging(app)

    # 注册错误处理
    register_error_handlers(app)

    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    return app


def register_blueprints(app):
    """注册蓝图"""
    app.register_blueprint(api_bp, url_prefix="/api")


def register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"status": "错误", "message": "内部服务器错误"}), 500

    @app.errorhandler(401)
    def handle_401(e):
        return jsonify({"status": "error", "message": "Unauthorized access"}), 401


def configure_logging(app):
    """配置日志"""
    if not app.debug and not app.testing:
        # 确保日志目录存在
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # 文件日志处理器
        file_handler = RotatingFileHandler(
            "logs/opinion_monitor.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)

        # 配置 app.logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Opinion monitor startup")

        # 配置根日志记录器（确保所有模块的日志都能写入文件）
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.INFO)


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
