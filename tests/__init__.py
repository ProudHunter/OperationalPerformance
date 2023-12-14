from flask_sqlalchemy import model

from app.run import app, db


class BaseTest:
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }

    @classmethod
    def setup_class(cls):
        with app.app_context():
            db.create_all()

    @classmethod
    def teardown_class(cls):
        with app.app_context():
            db.drop_all()

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        exclude_tables = []
        models = {
            m.__tablename__: m
            for m in db.Model.registry._class_registry.values()
            if isinstance(m, model.DefaultMeta)
        }
        tables = db.metadata.sorted_tables
        tables.reverse()
        with app.app_context():
            for table in tables:
                if table.name in exclude_tables:
                    continue
                db.session.query(models[table.name]).delete()
                db.session.commit()
