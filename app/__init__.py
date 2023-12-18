# 应用工厂目录



def register_logging(app):
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s P[%(process)d] T[%(thread)d] %(lineno)sL@%(filename)s:'
        ' %(message)s')

    handler = RotatingFileHandler("flask.log", maxBytes=1024000, backupCount=10)
    handler.setLevel(app.config.get("LOG_LEVEL"))
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    @app.before_request
    def log_each_request():
        app.logger.info(f"[{request.method}]{request.path} from {request.remote_addr}, params {request.args.to_dict()}, body {request.get_data()}")


def register_errors(app: Flask):
    @app.errorhandler(Exception)
    def framework_error(e):
        app.logger.error(str(e))
        app.logger.error(traceback.format_exc())
        if isinstance(e, APIException):  # 手动触发的异常
            return e
        elif isinstance(e, HTTPException):  # 代码异常
            return APIException(e.code, e.description, None)
        else:
            if app.config['DEBUG']:
                raise e
            else:
                return ServerError()

