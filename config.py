import os

from keeperService import getConnections, getEncryptionString

basedir = os.path.abspath(os.path.dirname(__file__))

class Config():

    SECRET_KEY = getEncryptionString()
    SSL_DISABLE = False

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True

    MAIL_SERVER = 'smtp.cern.ch'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    CDB_UPLOAD_MAIL_SUBJECT_PREFIX = '[myService]'
    CDB_UPLOAD_MAIL_SENDER         = 'me@example.com'
    CDB_UPLOAD_ADMIN               = os.environ.get('CDB_UPLOAD_ADMIN')
    CDB_UPLOAD_SLOW_DB_QUERY_TIME  = 0.5

    # Logging
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    LOGGING_DIR = os.path.join(BASE_DIR, 'logs/myService/')
    LOGGING_FILE = os.path.join(LOGGING_DIR, 'log')

    # EOS ROOT
    EOS_ROOT = "/eos/cms/store/group/alca_global/multiruns/results/jenkins"

    # get some DB connections from the secrets file (as they may contain credentials):
    # SQLALCHEMY_DATABASE_URI = getConnections( 'userDB' )
    SQLALCHEMY_DATABASE_URI = "sqlite:////afs/cern.ch/work/p/poramus/database/database.db"
    LOG_DB  = getConnections( 'logDB' )
    DEST_DB = getConnections( 'destDB' ).replace('oracle://','').replace(':', '/')     # 'cms_orcoff_prep/<pwd>@CMS_CONDITIONS_002'
    # RUN_INFO_DB = getConnections( 'runInfoDB' ) # 'oracle://cms_orcon_adg/CMS_CONDITIONS'

    # SQLALCHEMY_BINDS = {
    #     'log'  : LOG_DB,
    #     'user' : SQLALCHEMY_DATABASE_URI,
    #     'runInfo'  : RUN_INFO_DB,
    # }

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
    'testing'    : TestingConfig,
    'production' : ProductionConfig,

    'default'    : DevelopmentConfig,
    'private'    : DevelopmentConfig,
}
