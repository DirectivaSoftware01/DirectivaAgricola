from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Empresa, UsuarioAdministracion
from .forms import EmpresaForm


def configuracion_view(request):
    """Vista de configuración - mostrar formulario de login para administración"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        rfc = request.POST.get('rfc', '').strip()
        
        # Si hay RFC, redirigir al login normal
        if rfc:
            return redirect('core:login')
        
        # Validar usuario de administración
        try:
            usuario_admin = UsuarioAdministracion.objects.using('administracion').get(
                usuario=username, 
                activo=True
            )
            if usuario_admin.check_password(password):
                # Usuario válido, mostrar listado de empresas
                empresas = Empresa.objects.using('administracion').all()
                return render(request, 'administracion/empresas.html', {
                    'empresas': empresas,
                    'usuario_admin': usuario_admin
                })
            else:
                messages.error(request, 'Credenciales incorrectas.')
        except UsuarioAdministracion.DoesNotExist:
            messages.error(request, 'Usuario no encontrado o inactivo.')
        
        # Si hay error, mostrar el formulario de nuevo con errores
        return render(request, 'administracion/login_admin.html')
    
    # Mostrar formulario de login para administración
    return render(request, 'administracion/login_admin.html')


def empresas_view(request):
    """Listado de empresas"""
    empresas = Empresa.objects.using('administracion').all()
    return render(request, 'administracion/empresas.html', {
        'empresas': empresas
    })


def empresa_create_view(request):
    """Crear nueva empresa"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.save(using='administracion')
            
            # Crear la base de datos de la empresa
            try:
                from django.core.management import call_command
                # Extraer el RFC del nombre de la base de datos (Directiva_RFC -> RFC)
                rfc_from_db_name = empresa.db_name.replace('Directiva_', '')
                call_command('crear_empresa_simple', 
                           empresa.db_name,
                           razon_social=empresa.nombre,
                           rfc=rfc_from_db_name,
                           direccion=request.POST.get('direccion', ''),
                           telefono=request.POST.get('telefono', ''),
                           ciclo_actual=request.POST.get('ciclo_actual', ''))
                
                messages.success(request, f'Empresa "{empresa.nombre}" creada exitosamente con base de datos inicializada.')
            except Exception as e:
                messages.warning(request, f'Empresa "{empresa.nombre}" creada, pero hubo un error al inicializar la base de datos: {str(e)}')
            
            return redirect('administracion:empresas')
    else:
        form = EmpresaForm()
    
    return render(request, 'administracion/empresa_form.html', {
        'form': form,
        'title': 'Nueva Empresa'
    })


def empresa_detail_view(request, empresa_id):
    """Ver detalle de empresa"""
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    return render(request, 'administracion/empresa_detail.html', {
        'empresa': empresa
    })


def empresa_edit_view(request, empresa_id):
    """Editar empresa"""
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save(using='administracion')
            messages.success(request, f'Empresa "{empresa.nombre}" actualizada exitosamente.')
            return redirect('administracion:empresas')
    else:
        form = EmpresaForm(instance=empresa)
    
    return render(request, 'administracion/empresa_form.html', {
        'form': form,
        'title': f'Editar {empresa.nombre}',
        'empresa': empresa
    })


@require_http_methods(["POST"])
def empresa_toggle_suspend(request, empresa_id):
    """Suspender/Activar empresa"""
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    empresa.suspendido = not empresa.suspendido
    empresa.save(using='administracion')
    
    action = 'suspendida' if empresa.suspendido else 'activada'
    messages.success(request, f'Empresa "{empresa.nombre}" {action} exitosamente.')
    
    return redirect('administracion:empresas')
