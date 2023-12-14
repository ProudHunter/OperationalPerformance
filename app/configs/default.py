import os

ROOT_PATH = os.path.split(os.path.abspath(__name__))[0]

DEBUG = True
SECRET_KEY = 'vRjCtZZvxeJnSLIBQNEtXkIbDABLtFVVWXElPJ'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(
    os.path.join(ROOT_PATH, 'OperationalPerformance.db'))
SQLALCHEMY_TRACK_MODIFICATIONS = False
