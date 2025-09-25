from threading import local


_state = local()


def set_current_company_db(db_alias: str | None):
    _state.company_db = db_alias


def get_current_company_db() -> str | None:
    return getattr(_state, 'company_db', None)


class EmpresaRouter:
    """Router de BD: modelos de administracion -> 'administracion';
    modelos de core -> BD de empresa si está definida en el contexto del hilo.
    """

    app_label_admin = 'administracion'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label_admin:
            return 'administracion'
        db = get_current_company_db()
        return db or 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label_admin:
            return 'administracion'
        db = get_current_company_db()
        return db or 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label_admin:
            return db == 'administracion'
        # El resto de apps migran en la BD por defecto (plantilla);
        # las BDs de empresas se crean/cargan fuera del ciclo de migración global.
        return db == 'default'


