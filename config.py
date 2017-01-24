import os

from keeperService import getConnections, getEncryptionString
from backend.python.utils import dbConnection
from backend.python.utils import configReader

basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    SECRET_KEY = getEncryptionString()
    SSL_DISABLE = False

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_POOL_RECYCLE = 7200  # 2 hours, needed for Oracle

    MAIL_SERVER = 'smtp.cern.ch'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    CDB_UPLOAD_MAIL_SUBJECT_PREFIX = '[cmsDbMultiRunHarvesting]'
    CDB_UPLOAD_MAIL_SENDER = 'me@example.com'
    CDB_UPLOAD_ADMIN = os.environ.get('CDB_UPLOAD_ADMIN')
    CDB_UPLOAD_SLOW_DB_QUERY_TIME = 0.5

    # Logging
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    LOGGING_DIR = os.path.join(BASE_DIR, 'logs/cmsDbMultiRunHarvesting/')
    LOGGING_FILE = os.path.join(LOGGING_DIR, 'log')

    # env variable should be set before running the web application
    # in other case a default 'local' config is used
    multirun_config_path = os.getenv('MULTIRUN_CONFIG', 'resources/referenceBackendCfgs/local.yml')
    MULTIRUN_CFG = configReader.read(multirun_config_path)

    # get connection to DB from secrets
    SQLALCHEMY_DATABASE_URI = getConnections('multirunDB')

    # in case Oracle is used (almost always) make sure TNS file is present
    dbConnection.resolve_tns()

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.CDB_UPLOAD_MAIL_SENDER,
            toaddrs=[cls.CDB_UPLOAD_ADMIN],
            subject=cls.CDB_UPLOAD_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig,
    'private': DevelopmentConfig,
}
