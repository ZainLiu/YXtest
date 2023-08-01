class Config(object):
    """
    测试环境配置
    注：禁止尝试代码动态修改config参数
    """

    def __setattr__(self, key, value):
        raise AttributeError("修改属性失败，原因：不允许动态修改配置文件属性")

    def __call__(self, *args, **kwargs):
        return self

    # 系统配置
    APP_PROJECT_ID = 1
    APP_PROJECT_PW = ''
    APP_PORT = 5190
    APP_HOST = '0.0.0.0'
    APP_DATE_FORMAT = '%Y-%m-%d'
    APP_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    APP_GATEWAY_URL = 'http://127.0.0.1:6000/gateway'

    # session配置(redis)
    SESSION_PREFIX = 'PREFIX'

    # db配置
    DB_HOST = ''
    DB_PORT = 3306
    DB_DB = ''
    DB_USER = ''
    DB_PASSWORD = ''
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 300
    SQLALCHEMY_POOL_RECYCLE = 300

    # redis db 配置
    REDIS_DB_HOST = ''
    REDIS_DB_PORT = 6379
    REDIS_DB_DB = 1
    REDIS_DB_PASSWORD = ''

    # flask配置
    DEBUG = False
    SECRET_KEY = ""
    SESSION_USE_SIGNER = False
    SESSION_PERMANENT = False
