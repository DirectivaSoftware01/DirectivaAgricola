from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Empresa(models.Model):
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    db_name = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    suspendido = models.BooleanField(default=False)

    class Meta:
        db_table = 'empresas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rfc})"


class UsuarioAdministracion(models.Model):
    nombre = models.CharField(max_length=200)
    usuario = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=128)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios_administracion'
        ordering = ['nombre']

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.nombre} ({self.usuario})"


