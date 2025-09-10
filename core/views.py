from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
import json
from django.db.models import Sum, Count
from django.db import models
from django.contrib import messages
from datetime import datetime
from .models import Usuario, Cliente, RegimenFiscal, Proveedor, Transportista, LoteOrigen, ClasificacionGasto, CentroCosto, ProductoServicio, ConfiguracionSistema, Cultivo, Remision, RemisionDetalle, CuentaBancaria, PagoRemision, PresupuestoGasto, Presupuesto, PresupuestoDetalle, Gasto, GastoDetalle
from .forms import LoginForm, UsuarioForm, ClienteForm, ClienteSearchForm, RegimenFiscalForm, ProveedorForm, ProveedorSearchForm, TransportistaForm, TransportistaSearchForm, LoteOrigenForm, LoteOrigenSearchForm, ClasificacionGastoForm, ClasificacionGastoSearchForm, CentroCostoForm, CentroCostoSearchForm, ProductoServicioForm, ProductoServicioSearchForm, ConfiguracionSistemaForm, CultivoForm, CultivoSearchForm, RemisionForm, RemisionDetalleForm, RemisionSearchForm, RemisionLiquidacionForm, RemisionCancelacionForm, CobranzaSearchForm, PresupuestoGastoForm, PresupuestoGastoSearchForm, PresupuestoForm, PresupuestoDetalleForm, PresupuestoSearchForm, GastoForm, GastoDetalleForm

# Create your views here.

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Directiva Agrícola - Dashboard'
        
        # Obtener estadísticas del dashboard
        context['clientes_activos'] = Cliente.objects.filter(activo=True).count()
        context['total_clientes'] = Cliente.objects.count()
        context['usuarios_activos'] = Usuario.objects.filter(is_active=True).count()
        
        return context

def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('core:dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    """Vista de logout"""
    logout(request)
    return redirect('core:login')

class ConfiguracionView(LoginRequiredMixin, ListView):
    """Vista para listar usuarios en configuración"""
    model = Usuario
    template_name = 'core/configuracion.html'
    context_object_name = 'usuarios'
    
    def dispatch(self, request, *args, **kwargs):
        # Asegurar autenticación antes de verificar permisos
        if not request.user.is_authenticated:
            return redirect('core:login')
        # Verificar que el usuario tenga permisos de administrador
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para acceder a la configuración de usuarios.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Usuario.objects.all().order_by('nombre')

class UsuarioCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear usuarios"""
    model = Usuario
    form_class = UsuarioForm
    template_name = 'core/usuario_form.html'
    success_url = reverse_lazy('core:configuracion')
    
    def form_valid(self, form):
        try:
            # Validar que el usuario actual tenga permisos de administrador
            if not self.request.user.is_admin and not self.request.user.is_superuser:
                messages.error(self.request, 'No tiene permisos para crear usuarios.')
                return redirect('core:configuracion')
            
            response = super().form_valid(form)
            messages.success(self.request, f'Usuario "{form.instance.username}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear usuario: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)

class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar usuarios"""
    model = Usuario
    form_class = UsuarioForm
    template_name = 'core/usuario_form.html'
    success_url = reverse_lazy('core:configuracion')
    
    def form_valid(self, form):
        try:
            # Validar que el usuario actual tenga permisos de administrador
            if not self.request.user.is_admin and not self.request.user.is_superuser:
                messages.error(self.request, 'No tiene permisos para editar usuarios.')
                return redirect('core:configuracion')
            
            # Prevenir que un usuario se edite a sí mismo para quitarse los permisos de admin
            if (self.object == self.request.user and 
                not form.cleaned_data.get('is_admin') and 
                self.request.user.is_admin):
                messages.error(self.request, 'No puede quitarse sus propios permisos de administrador.')
                return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, f'Usuario "{form.instance.username}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar usuario: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)

class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar usuarios"""
    model = Usuario
    template_name = 'core/usuario_confirm_delete.html'
    success_url = reverse_lazy('core:configuracion')
    
    def delete(self, request, *args, **kwargs):
        try:
            # Validar que el usuario actual tenga permisos de administrador
            if not self.request.user.is_admin and not self.request.user.is_superuser:
                messages.error(self.request, 'No tiene permisos para eliminar usuarios.')
                return redirect('core:configuracion')
            
            # Prevenir que un usuario se elimine a sí mismo
            if self.object == self.request.user:
                messages.error(self.request, 'No puede eliminarse a sí mismo.')
                return redirect('core:configuracion')
            
            # Prevenir eliminar el último administrador
            if self.object.is_admin:
                admin_count = Usuario.objects.filter(is_admin=True).count()
                if admin_count <= 1:
                    messages.error(self.request, 'No se puede eliminar el último administrador del sistema.')
                    return redirect('core:configuracion')
            
            username = self.object.username
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Usuario "{username}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar usuario: {str(e)}')
            return redirect('core:configuracion')


# ===========================
# VISTAS PARA CRUD DE CLIENTES
# ===========================

class ClienteListView(LoginRequiredMixin, ListView):
    """Vista para listar clientes con búsqueda y filtros"""
    model = Cliente
    template_name = 'core/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cliente.objects.select_related('regimen_fiscal', 'usuario_creacion').all()
        
        # Obtener parámetros de búsqueda
        form = ClienteSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            regimen_fiscal = form.cleaned_data.get('regimen_fiscal')
            activo = form.cleaned_data.get('activo')
            
            # Filtrar por búsqueda
            if busqueda:
                queryset = queryset.filter(
                    Q(razon_social__icontains=busqueda) |
                    Q(rfc__icontains=busqueda) |
                    Q(codigo__icontains=busqueda)
                )
            
            # Filtrar por régimen fiscal
            if regimen_fiscal:
                queryset = queryset.filter(regimen_fiscal=regimen_fiscal)
            
            # Filtrar por estado activo
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClienteSearchForm(self.request.GET)
        context['title'] = 'Gestión de Clientes'
        return context


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear clientes"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'core/cliente_form.html'
    success_url = reverse_lazy('core:cliente_list')
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que crea el registro
            form.instance.usuario_creacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Cliente "{form.instance.razon_social}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear cliente: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Cliente'
        return context


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar clientes"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'core/cliente_form.html'
    success_url = reverse_lazy('core:cliente_list')
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que modifica el registro
            form.instance.usuario_modificacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Cliente "{form.instance.razon_social}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar cliente: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Cliente: {self.object.razon_social}'
        return context


class ClienteDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar detalles de un cliente"""
    template_name = 'core/cliente_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = get_object_or_404(Cliente, pk=kwargs['pk'])
        context['cliente'] = cliente
        context['title'] = f'Cliente: {cliente.razon_social}'
        return context


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar clientes"""
    model = Cliente
    template_name = 'core/cliente_confirm_delete.html'
    success_url = reverse_lazy('core:cliente_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            cliente = self.get_object()
            razon_social = cliente.razon_social
            
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Cliente "{razon_social}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar cliente: {str(e)}')
            return redirect('core:cliente_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Cliente: {self.object.razon_social}'
        return context


# ====================================
# VISTAS PARA CRUD DE RÉGIMEN FISCAL
# ====================================

class RegimenFiscalListView(LoginRequiredMixin, ListView):
    """Vista para listar regímenes fiscales"""
    model = RegimenFiscal
    template_name = 'core/regimen_fiscal_list.html'
    context_object_name = 'regimenes'
    paginate_by = 20
    
    def get_queryset(self):
        return RegimenFiscal.objects.all().order_by('codigo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Regímenes Fiscales'
        return context


class RegimenFiscalCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear regímenes fiscales"""
    model = RegimenFiscal
    form_class = RegimenFiscalForm
    template_name = 'core/regimen_fiscal_form.html'
    success_url = reverse_lazy('core:regimen_fiscal_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores pueden gestionar regímenes fiscales
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para gestionar regímenes fiscales.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'Régimen fiscal "{form.instance.codigo}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear régimen fiscal: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Régimen Fiscal'
        return context


class RegimenFiscalUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar regímenes fiscales"""
    model = RegimenFiscal
    form_class = RegimenFiscalForm
    template_name = 'core/regimen_fiscal_form.html'
    success_url = reverse_lazy('core:regimen_fiscal_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores pueden gestionar regímenes fiscales
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para gestionar regímenes fiscales.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'Régimen fiscal "{form.instance.codigo}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar régimen fiscal: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Régimen Fiscal: {self.object.codigo}'
        return context


class RegimenFiscalDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar regímenes fiscales"""
    model = RegimenFiscal
    template_name = 'core/regimen_fiscal_confirm_delete.html'
    success_url = reverse_lazy('core:regimen_fiscal_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores pueden gestionar regímenes fiscales
        if not getattr(request.user, 'is_admin', False) and not request.user.is_superuser:
            messages.error(request, 'No tiene permisos para gestionar regímenes fiscales.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            regimen = self.get_object()
            
            # Verificar si hay clientes usando este régimen fiscal
            clientes_count = Cliente.objects.filter(regimen_fiscal=regimen).count()
            if clientes_count > 0:
                messages.error(
                    self.request, 
                    f'No se puede eliminar el régimen fiscal "{regimen.codigo}" porque está siendo usado por {clientes_count} cliente(s).'
                )
                return redirect('core:regimen_fiscal_list')
            
            codigo = regimen.codigo
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Régimen fiscal "{codigo}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar régimen fiscal: {str(e)}')
            return redirect('core:regimen_fiscal_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Régimen Fiscal: {self.object.codigo}'
        return context


# ===========================
# VISTAS PARA CRUD DE PROVEEDORES
# ===========================

class ProveedorListView(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = 'core/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Proveedor.objects.select_related('usuario_creacion').all()
        form = ProveedorSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(nombre__icontains=busqueda) | 
                    Q(rfc__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProveedorSearchForm(self.request.GET)
        context['title'] = 'Gestión de Proveedores'
        return context


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'core/proveedor_form.html'
    success_url = reverse_lazy('core:proveedor_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Proveedor "{form.instance.nombre}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear proveedor: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Proveedor'
        context['is_edit'] = False
        return context


class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'core/proveedor_form.html'
    success_url = reverse_lazy('core:proveedor_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Proveedor "{form.instance.nombre}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar proveedor: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Proveedor: {self.object.nombre}'
        context['is_edit'] = True
        return context


class ProveedorDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/proveedor_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proveedor = get_object_or_404(Proveedor, pk=kwargs['pk'])
        context['proveedor'] = proveedor
        context['title'] = f'Proveedor: {proveedor.nombre}'
        return context


class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Proveedor
    template_name = 'core/proveedor_confirm_delete.html'
    success_url = reverse_lazy('core:proveedor_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            proveedor = self.get_object()
            nombre = proveedor.nombre
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Proveedor "{nombre}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar proveedor: {str(e)}')
            return redirect('core:proveedor_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Proveedor: {self.object.nombre}'
        return context


# ===========================
# VISTAS PARA CRUD DE TRANSPORTISTAS
# ===========================

class TransportistaListView(LoginRequiredMixin, ListView):
    model = Transportista
    template_name = 'core/transportista_list.html'
    context_object_name = 'transportistas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Transportista.objects.select_related('usuario_creacion').all()
        form = TransportistaSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(nombre_completo__icontains=busqueda) | 
                    Q(licencia__icontains=busqueda) | 
                    Q(placas_unidad__icontains=busqueda) |
                    Q(placas_remolque__icontains=busqueda) |
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TransportistaSearchForm(self.request.GET)
        context['title'] = 'Gestión de Transportistas'
        return context


class TransportistaCreateView(LoginRequiredMixin, CreateView):
    model = Transportista
    form_class = TransportistaForm
    template_name = 'core/transportista_form.html'
    success_url = reverse_lazy('core:transportista_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Transportista "{form.instance.nombre_completo}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear transportista: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Transportista'
        context['is_edit'] = False
        return context


class TransportistaUpdateView(LoginRequiredMixin, UpdateView):
    model = Transportista
    form_class = TransportistaForm
    template_name = 'core/transportista_form.html'
    success_url = reverse_lazy('core:transportista_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Transportista "{form.instance.nombre_completo}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar transportista: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Transportista: {self.object.nombre_completo}'
        context['is_edit'] = True
        return context


class TransportistaDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/transportista_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transportista = get_object_or_404(Transportista, pk=kwargs['pk'])
        context['transportista'] = transportista
        context['title'] = f'Transportista: {transportista.nombre_completo}'
        return context


class TransportistaDeleteView(LoginRequiredMixin, DeleteView):
    model = Transportista
    template_name = 'core/transportista_confirm_delete.html'
    success_url = reverse_lazy('core:transportista_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            transportista = self.get_object()
            nombre = transportista.nombre_completo
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Transportista "{nombre}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar transportista: {str(e)}')
            return redirect('core:transportista_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Transportista: {self.object.nombre_completo}'
        return context


# ===========================
# VISTAS PARA CRUD DE LOTES - ORIGEN
# ===========================

class LoteOrigenListView(LoginRequiredMixin, ListView):
    model = LoteOrigen
    template_name = 'core/lote_origen_list.html'
    context_object_name = 'lotes_origen'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = LoteOrigen.objects.select_related('usuario_creacion').all()
        form = LoteOrigenSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(nombre__icontains=busqueda) | 
                    Q(observaciones__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LoteOrigenSearchForm(self.request.GET)
        context['title'] = 'Gestión de Lotes - Origen'
        return context


class LoteOrigenCreateView(LoginRequiredMixin, CreateView):
    model = LoteOrigen
    form_class = LoteOrigenForm
    template_name = 'core/lote_origen_form.html'
    success_url = reverse_lazy('core:lote_origen_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Lote de origen "{form.instance.nombre}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear lote de origen: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Lote de Origen'
        context['is_edit'] = False
        return context


class LoteOrigenUpdateView(LoginRequiredMixin, UpdateView):
    model = LoteOrigen
    form_class = LoteOrigenForm
    template_name = 'core/lote_origen_form.html'
    success_url = reverse_lazy('core:lote_origen_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Lote de origen "{form.instance.nombre}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar lote de origen: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Lote de Origen: {self.object.nombre}'
        context['is_edit'] = True
        return context


class LoteOrigenDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/lote_origen_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lote_origen = get_object_or_404(LoteOrigen, pk=kwargs['pk'])
        context['lote_origen'] = lote_origen
        context['title'] = f'Lote de Origen: {lote_origen.nombre}'
        return context


class LoteOrigenDeleteView(LoginRequiredMixin, DeleteView):
    model = LoteOrigen
    template_name = 'core/lote_origen_confirm_delete.html'
    success_url = reverse_lazy('core:lote_origen_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            lote_origen = self.get_object()
            nombre = lote_origen.nombre
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Lote de origen "{nombre}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar lote de origen: {str(e)}')
            return redirect('core:lote_origen_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Lote de Origen: {self.object.nombre}'
        return context


# ===========================
# VISTAS PARA CRUD DE CLASIFICACIÓN DE GASTOS
# ===========================

class ClasificacionGastoListView(LoginRequiredMixin, ListView):
    model = ClasificacionGasto
    template_name = 'core/clasificacion_gasto_list.html'
    context_object_name = 'clasificaciones_gasto'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ClasificacionGasto.objects.select_related('usuario_creacion').all()
        form = ClasificacionGastoSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(descripcion__icontains=busqueda) | 
                    Q(observaciones__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClasificacionGastoSearchForm(self.request.GET)
        context['title'] = 'Gestión de Clasificación de Gastos'
        return context


class ClasificacionGastoCreateView(LoginRequiredMixin, CreateView):
    model = ClasificacionGasto
    form_class = ClasificacionGastoForm
    template_name = 'core/clasificacion_gasto_form.html'
    success_url = reverse_lazy('core:clasificacion_gasto_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Clasificación de gasto "{form.instance.descripcion}" creada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear clasificación de gasto: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nueva Clasificación de Gasto'
        context['is_edit'] = False
        return context


class ClasificacionGastoUpdateView(LoginRequiredMixin, UpdateView):
    model = ClasificacionGasto
    form_class = ClasificacionGastoForm
    template_name = 'core/clasificacion_gasto_form.html'
    success_url = reverse_lazy('core:clasificacion_gasto_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Clasificación de gasto "{form.instance.descripcion}" actualizada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar clasificación de gasto: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Clasificación de Gasto: {self.object.descripcion}'
        context['is_edit'] = True
        return context


class ClasificacionGastoDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/clasificacion_gasto_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clasificacion_gasto = get_object_or_404(ClasificacionGasto, pk=kwargs['pk'])
        context['clasificacion_gasto'] = clasificacion_gasto
        context['title'] = f'Clasificación de Gasto: {clasificacion_gasto.descripcion}'
        return context


class ClasificacionGastoDeleteView(LoginRequiredMixin, DeleteView):
    model = ClasificacionGasto
    template_name = 'core/clasificacion_gasto_confirm_delete.html'
    success_url = reverse_lazy('core:clasificacion_gasto_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            clasificacion_gasto = self.get_object()
            descripcion = clasificacion_gasto.descripcion
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Clasificación de gasto "{descripcion}" eliminada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar clasificación de gasto: {str(e)}')
            return redirect('core:clasificacion_gasto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Clasificación de Gasto: {self.object.descripcion}'
        return context


# ===========================
# VISTAS PARA CRUD DE CENTRO DE COSTOS
# ===========================

class CentroCostoListView(LoginRequiredMixin, ListView):
    model = CentroCosto
    template_name = 'core/centro_costo_list.html'
    context_object_name = 'centros_costo'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CentroCosto.objects.select_related('usuario_creacion').all()
        form = CentroCostoSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(descripcion__icontains=busqueda) | 
                    Q(observaciones__icontains=busqueda) | 
                    Q(codigo__icontains=busqueda)
                )
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = CentroCostoSearchForm(self.request.GET)
        context['title'] = 'Gestión de Centros de Costos'
        return context


class CentroCostoCreateView(LoginRequiredMixin, CreateView):
    model = CentroCosto
    form_class = CentroCostoForm
    template_name = 'core/centro_costo_form.html'
    success_url = reverse_lazy('core:centro_costo_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Centro de costo "{form.instance.descripcion}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear centro de costo: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Centro de Costo'
        context['is_edit'] = False
        return context


class CentroCostoUpdateView(LoginRequiredMixin, UpdateView):
    model = CentroCosto
    form_class = CentroCostoForm
    template_name = 'core/centro_costo_form.html'
    success_url = reverse_lazy('core:centro_costo_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'Centro de costo "{form.instance.descripcion}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar centro de costo: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Centro de Costo: {self.object.descripcion}'
        context['is_edit'] = True
        return context


class CentroCostoDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/centro_costo_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro_costo = get_object_or_404(CentroCosto, pk=kwargs['pk'])
        context['centro_costo'] = centro_costo
        context['title'] = f'Centro de Costo: {centro_costo.descripcion}'
        return context


class CentroCostoDeleteView(LoginRequiredMixin, DeleteView):
    model = CentroCosto
    template_name = 'core/centro_costo_confirm_delete.html'
    success_url = reverse_lazy('core:centro_costo_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            centro_costo = self.get_object()
            descripcion = centro_costo.descripcion
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Centro de costo "{descripcion}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar centro de costo: {str(e)}')
            return redirect('core:centro_costo_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Centro de Costo: {self.object.descripcion}'
        return context


# ===========================
# VISTAS PARA CRUD DE PRODUCTOS Y SERVICIOS
# ===========================

class ProductoServicioListView(LoginRequiredMixin, ListView):
    model = ProductoServicio
    template_name = 'core/producto_servicio_list.html'
    context_object_name = 'productos_servicios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProductoServicio.objects.select_related('usuario_creacion').all()
        form = ProductoServicioSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            tipo = form.cleaned_data.get('tipo')
            activo = form.cleaned_data.get('activo')
            
            if busqueda:
                queryset = queryset.filter(
                    Q(sku__icontains=busqueda) | 
                    Q(descripcion__icontains=busqueda) | 
                    Q(clave_sat__icontains=busqueda) |
                    Q(codigo__icontains=busqueda)
                )
            
            if tipo != '':
                queryset = queryset.filter(producto_servicio=tipo == '1')
            
            if activo != '':
                queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductoServicioSearchForm(self.request.GET)
        context['title'] = 'Gestión de Productos y Servicios'
        return context


class ProductoServicioCreateView(LoginRequiredMixin, CreateView):
    model = ProductoServicio
    form_class = ProductoServicioForm
    template_name = 'core/producto_servicio_form.html'
    success_url = reverse_lazy('core:producto_servicio_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_creacion = self.request.user
            response = super().form_valid(form)
            tipo = "Producto" if form.instance.producto_servicio else "Servicio"
            messages.success(self.request, f'{tipo} "{form.instance.descripcion}" creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear producto o servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Producto o Servicio'
        context['is_edit'] = False
        return context


class ProductoServicioUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductoServicio
    form_class = ProductoServicioForm
    template_name = 'core/producto_servicio_form.html'
    success_url = reverse_lazy('core:producto_servicio_list')
    
    def form_valid(self, form):
        try:
            form.instance.usuario_modificacion = self.request.user
            response = super().form_valid(form)
            tipo = "Producto" if form.instance.producto_servicio else "Servicio"
            messages.success(self.request, f'{tipo} "{form.instance.descripcion}" actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar producto o servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = "Producto" if self.object.producto_servicio else "Servicio"
        context['title'] = f'Editar {tipo}: {self.object.descripcion}'
        context['is_edit'] = True
        return context


class ProductoServicioDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'core/producto_servicio_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto_servicio = get_object_or_404(ProductoServicio, pk=kwargs['pk'])
        context['producto_servicio'] = producto_servicio
        tipo = "Producto" if producto_servicio.producto_servicio else "Servicio"
        context['title'] = f'{tipo}: {producto_servicio.descripcion}'
        return context


class ProductoServicioDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductoServicio
    template_name = 'core/producto_servicio_confirm_delete.html'
    success_url = reverse_lazy('core:producto_servicio_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            producto_servicio = self.get_object()
            descripcion = producto_servicio.descripcion
            tipo = "Producto" if producto_servicio.producto_servicio else "Servicio"
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'{tipo} "{descripcion}" eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar producto o servicio: {str(e)}')
            return redirect('core:producto_servicio_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = "Producto" if self.object.producto_servicio else "Servicio"
        context['title'] = f'Eliminar {tipo}: {self.object.descripcion}'
        return context
# Vistas para Configuración del Sistema

class ConfiguracionSistemaView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar y editar la configuración del sistema"""
    template_name = 'core/configuracion_sistema.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Configuración del Sistema'
        
        # Obtener la configuración del sistema
        configuracion = ConfiguracionSistema.objects.first()
        
        # Si no existe configuración, crear una instancia vacía para el formulario
        if not configuracion:
            configuracion = ConfiguracionSistema()
        
        # Crear el formulario con la configuración existente
        form = ConfiguracionSistemaForm(instance=configuracion)
        
        context['configuracion'] = configuracion
        context['form'] = form
        
        # Agregar información sobre certificados existentes
        context['tiene_certificado'] = bool(configuracion and configuracion.certificado)
        context['tiene_llave'] = bool(configuracion and configuracion.llave)
        context['tiene_password'] = bool(configuracion and configuracion.password_llave)
        context['certificado_nombre'] = configuracion.certificado_nombre if configuracion else ''
        context['llave_nombre'] = configuracion.llave_nombre if configuracion else ''
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Manejar el envío del formulario"""
        try:
            configuracion = ConfiguracionSistema.objects.first()
            
            # Verificar si es un guardado parcial por sección
            seccion = request.POST.get('seccion')
            
            if seccion:
                # Guardado parcial por sección
                if seccion == 'ciclo':
                    if 'ciclo_actual' in request.POST:
                        if not configuracion:
                            configuracion = ConfiguracionSistema()
                        configuracion.ciclo_actual = request.POST.get('ciclo_actual')
                        if not configuracion.pk:
                            configuracion.usuario_creacion = request.user
                        else:
                            configuracion.usuario_modificacion = request.user
                        configuracion.save()
                        messages.success(request, 'Ciclo de producción guardado correctamente.')
                
                elif seccion == 'empresa':
                    if not configuracion:
                        configuracion = ConfiguracionSistema()
                    
                    if 'razon_social' in request.POST:
                        configuracion.razon_social = request.POST.get('razon_social')
                    if 'rfc' in request.POST:
                        configuracion.rfc = request.POST.get('rfc')
                    if 'direccion' in request.POST:
                        configuracion.direccion = request.POST.get('direccion')
                if 'telefono' in request.POST:
                    configuracion.telefono = request.POST.get('telefono')
                if 'logo_empresa' in request.FILES:
                    print(f"DEBUG: Archivo logo_empresa encontrado: {request.FILES.get('logo_empresa').name}")
                    configuracion.logo_empresa = request.FILES.get('logo_empresa')
                else:
                    print("DEBUG: No se encontró logo_empresa en request.FILES")
                    print(f"DEBUG: Archivos disponibles: {list(request.FILES.keys())}")
                
                if not configuracion.pk:
                    configuracion.usuario_creacion = request.user
                else:
                    configuracion.usuario_modificacion = request.user
                configuracion.save()
                messages.success(request, 'Datos de la empresa guardados correctamente.')
                
            elif seccion == 'timbrado':
                if not configuracion:
                    configuracion = ConfiguracionSistema()
                
                if 'nombre_pac' in request.POST:
                    configuracion.nombre_pac = request.POST.get('nombre_pac')
                if 'contrato' in request.POST:
                    configuracion.contrato = request.POST.get('contrato')
                if 'usuario_pac' in request.POST:
                    configuracion.usuario_pac = request.POST.get('usuario_pac')
                if 'password_pac' in request.POST:
                    configuracion.password_pac = request.POST.get('password_pac')
                
                if not configuracion.pk:
                    configuracion.usuario_creacion = request.user
                else:
                    configuracion.usuario_modificacion = request.user
                configuracion.save()
                messages.success(request, 'Configuración de timbrado guardada correctamente.')
                
            elif seccion == 'certificados':
                if not configuracion:
                    configuracion = ConfiguracionSistema()
                
                # Procesar archivos de certificado y llave
                if 'certificado_file' in request.FILES:
                    certificado_file = request.FILES.get('certificado_file')
                    # Convertir archivo a base64
                    import base64
                    configuracion.certificado = base64.b64encode(certificado_file.read()).decode('utf-8')
                    # Guardar nombre del archivo original
                    configuracion.certificado_nombre = certificado_file.name
                
                if 'llave_file' in request.FILES:
                    llave_file = request.FILES.get('llave_file')
                    # Convertir archivo a base64
                    import base64
                    configuracion.llave = base64.b64encode(llave_file.read()).decode('utf-8')
                    # Guardar nombre del archivo original
                    configuracion.llave_nombre = llave_file.name
                
                if 'password_llave' in request.POST:
                    configuracion.password_llave = request.POST.get('password_llave')
                
                if not configuracion.pk:
                    configuracion.usuario_creacion = request.user
                else:
                    configuracion.usuario_modificacion = request.user
                configuracion.save()
                messages.success(request, 'Certificados guardados correctamente.')
                
                # Si es una petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Sección guardada correctamente'})
                
                return redirect('core:configuracion_sistema')
            
            else:
                # Guardado completo del formulario
                form = ConfiguracionSistemaForm(request.POST, request.FILES, instance=configuracion)
                
                if form.is_valid():
                    configuracion = form.save(commit=False)
                    
                    # Si es una nueva configuración, asignar usuario de creación
                    if not configuracion.pk:
                        configuracion.usuario_creacion = request.user
                    else:
                        configuracion.usuario_modificacion = request.user
                    
                    configuracion.save()
                    
                    messages.success(request, 'Configuración guardada correctamente.')
                    return redirect('core:configuracion_sistema')
                else:
                    # Mostrar errores específicos del formulario
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            error_messages.append(f"{form.fields[field].label}: {error}")
                    
                    if error_messages:
                        messages.error(request, f'Errores en el formulario: {"; ".join(error_messages)}')
                    else:
                        messages.error(request, 'Por favor, corrija los errores en el formulario.')
                
        except Exception as e:
            messages.error(request, f'Error al guardar la configuración: {str(e)}')
        
        context = self.get_context_data()
        # Crear el formulario con la configuración existente
        configuracion = ConfiguracionSistema.objects.first()
        if not configuracion:
            configuracion = ConfiguracionSistema()
        form = ConfiguracionSistemaForm(instance=configuracion)
        context['form'] = form
        return render(request, self.template_name, context)

# Vistas para Cultivos

class CultivoListView(LoginRequiredMixin, ListView):
    """Vista para listar cultivos"""
    model = Cultivo
    template_name = 'core/cultivo_list.html'
    context_object_name = 'cultivos'
    paginate_by = 10
    
    def get_queryset(self):
        """Filtrar cultivos según los parámetros de búsqueda"""
        queryset = Cultivo.objects.all()
        search = self.request.GET.get('search')
        activo = self.request.GET.get('activo')
        
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(variedad__icontains=search)
            )
        
        if activo:
            queryset = queryset.filter(activo=activo == '1')
        
        return queryset.order_by('nombre', 'variedad')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cultivos'
        context['search_form'] = CultivoSearchForm(self.request.GET)
        return context


class CultivoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear cultivos"""
    model = Cultivo
    form_class = CultivoForm
    template_name = 'core/cultivo_form.html'
    success_url = reverse_lazy('core:cultivo_list')
    
    def form_valid(self, form):
        """Asignar usuario de creación"""
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, 'Cultivo creado correctamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Cultivo'
        context['is_edit'] = False
        return context


class CultivoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar cultivos"""
    model = Cultivo
    form_class = CultivoForm
    template_name = 'core/cultivo_form.html'
    success_url = reverse_lazy('core:cultivo_list')
    
    def form_valid(self, form):
        """Asignar usuario de modificación"""
        form.instance.usuario_modificacion = self.request.user
        messages.success(self.request, 'Cultivo actualizado correctamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Cultivo: {self.object.nombre} - {self.object.variedad}'
        context['is_edit'] = True
        return context


class CultivoDetailView(LoginRequiredMixin, TemplateView):
    """Vista para ver detalles de un cultivo"""
    template_name = 'core/cultivo_detail.html'
    
    def get_object(self):
        return get_object_or_404(Cultivo, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cultivo = self.get_object()
        context['cultivo'] = cultivo
        context['title'] = f'Cultivo: {cultivo.nombre} - {cultivo.variedad}'
        return context


class CultivoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar cultivos"""
    model = Cultivo
    template_name = 'core/cultivo_confirm_delete.html'
    success_url = reverse_lazy('core:cultivo_list')
    
    def delete(self, request, *args, **kwargs):
        """Eliminar con mensaje de confirmación"""
        try:
            self.object = self.get_object()
            nombre = f"{self.object.nombre} - {self.object.variedad}"
            self.object.delete()
            messages.success(request, f'Cultivo "{nombre}" eliminado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar cultivo: {str(e)}')
        return redirect('core:cultivo_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Cultivo: {self.object.nombre} - {self.object.variedad}'
        return context


# ===========================
# VISTAS PARA CRUD DE REMISIONES
# ===========================

class RemisionListView(LoginRequiredMixin, ListView):
    """Vista para listar remisiones con búsqueda y filtros"""
    model = Remision
    template_name = 'core/remision_list.html'
    context_object_name = 'remisiones'
    paginate_by = 20
    
    def get_queryset(self):
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Filtrar por ciclo actual si está configurado
        if ciclo_actual:
            queryset = Remision.objects.select_related(
                'cliente', 'lote_origen', 'transportista', 'usuario_creacion'
            ).filter(ciclo=ciclo_actual)
        else:
            queryset = Remision.objects.select_related(
                'cliente', 'lote_origen', 'transportista', 'usuario_creacion'
            ).all()
        
        # Obtener parámetros de búsqueda
        form = RemisionSearchForm(self.request.GET)
        
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            cliente = form.cleaned_data.get('cliente')
            lote_origen = form.cleaned_data.get('lote_origen')
            transportista = form.cleaned_data.get('transportista')
            fecha_desde = form.cleaned_data.get('fecha_desde')
            fecha_hasta = form.cleaned_data.get('fecha_hasta')
            
            # Filtrar por búsqueda
            if busqueda:
                queryset = queryset.filter(
                    Q(ciclo__icontains=busqueda) |
                    Q(folio__icontains=busqueda) |
                    Q(cliente__razon_social__icontains=busqueda) |
                    Q(observaciones__icontains=busqueda)
                )
            
            # Filtrar por cliente
            if cliente:
                queryset = queryset.filter(cliente=cliente)
            
            # Filtrar por lote origen
            if lote_origen:
                queryset = queryset.filter(lote_origen=lote_origen)
            
            # Filtrar por transportista
            if transportista:
                queryset = queryset.filter(transportista=transportista)
            
            # Filtrar por rango de fechas
            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RemisionSearchForm(self.request.GET)
        context['title'] = 'Gestión de Remisiones'
        
        # Agregar ciclo actual al contexto
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


class RemisionCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear remisiones"""
    model = Remision
    form_class = RemisionForm
    template_name = 'core/remision_form.html'
    success_url = reverse_lazy('core:remision_list')
    
    def form_valid(self, form):
        try:
            # Verificar que se hayan agregado detalles antes de crear la remisión
            detalles_count = self.request.POST.get('detalles_count', 0)
            try:
                detalles_count = int(detalles_count)
            except (ValueError, TypeError):
                detalles_count = 0
            
            if detalles_count == 0:
                messages.error(self.request, 'No se puede crear una remisión sin detalles. Por favor, agregue al menos un detalle en la pestaña "Detalles de la Remisión".')
                return self.form_invalid(form)
            
            # Asignar el usuario que crea el registro
            form.instance.usuario_creacion = self.request.user
            
            # Obtener el ciclo actual de la configuración
            from .models import ConfiguracionSistema
            configuracion = ConfiguracionSistema.objects.first()
            if configuracion and configuracion.ciclo_actual:
                form.instance.ciclo = configuracion.ciclo_actual
            
            # Guardar la remisión primero
            response = super().form_valid(form)
            
            # Ahora crear los detalles temporales
            self.crear_detalles_temporales(form.instance)
            
            messages.success(self.request, f'Remisión "{form.instance.ciclo} - {form.instance.folio:06d}" creada exitosamente con {detalles_count} detalle(s).')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear remisión: {str(e)}')
            return self.form_invalid(form)
    
    def crear_detalles_temporales(self, remision):
        """Crear los detalles temporales que se enviaron desde el frontend"""
        import json
        
        # Obtener los detalles temporales del POST (enviados como JSON)
        detalles_json = self.request.POST.get('detalles_temporales', '[]')
        try:
            detalles_data = json.loads(detalles_json)
        except (json.JSONDecodeError, TypeError):
            detalles_data = []
        
        # Crear cada detalle
        for detalle_data in detalles_data:
            try:
                from .models import RemisionDetalle, Cultivo
                
                # Obtener el cultivo
                cultivo = Cultivo.objects.get(pk=detalle_data['cultivo']['id'])
                
                # Crear el detalle (el peso_promedio se calcula automáticamente en el método save)
                detalle = RemisionDetalle.objects.create(
                    remision=remision,
                    cultivo=cultivo,
                    calidad=detalle_data['calidad'],
                    no_arps=detalle_data['no_arps'],
                    kgs_enviados=round(detalle_data['kgs_enviados'], 2),
                    merma_arps=detalle_data['merma_arps'],
                    kgs_liquidados=round(detalle_data['kgs_liquidados'], 2),
                    kgs_merma=round(detalle_data['kgs_merma'], 2),
                    precio=round(detalle_data['precio'], 2),
                    importe_liquidado=round(detalle_data['importe_liquidado'], 2),
                    usuario_creacion=self.request.user
                )
            except Exception as e:
                # Si hay error creando un detalle, continuar con los demás
                print(f"Error creando detalle: {e}")
                continue


def get_cultivos_ajax(request):
    """Vista AJAX para obtener cultivos activos"""
    if request.method == 'GET':
        cultivos = Cultivo.objects.filter(activo=True).values('codigo', 'nombre', 'variedad')
        # Renombrar 'codigo' a 'id' para el frontend
        cultivos_data = []
        for cultivo in cultivos:
            cultivos_data.append({
                'id': cultivo['codigo'],
                'nombre': cultivo['nombre'],
                'variedad': cultivo['variedad']
            })
        return JsonResponse(cultivos_data, safe=False)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


class RemisionLiquidacionView(LoginRequiredMixin, TemplateView):
    """Vista para preliquidar una remisión"""
    template_name = 'core/remision_liquidacion.html'
    
    def get_object(self):
        """Obtener la remisión a preliquidar"""
        return get_object_or_404(Remision, pk=self.kwargs['pk'])
    
    def get(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de permitir la preliquidación"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede preliquidar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = self.get_object()
        context['title'] = f'Liquidar Remisión {self.object.ciclo} - {self.object.folio:06d}'
        context['remision'] = self.object
        context['detalles'] = self.object.detalles.all()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar la liquidación"""
        self.object = self.get_object()
        
        # Verificar que la remisión no esté ya preliquidada
        if self.esta_liquidada(self.object):
            messages.error(request, 'Esta remisión ya ha sido preliquidada.')
            return redirect('core:remision_list')
        
        # Verificar que la remisión no esté cancelada
        if self.object.cancelada:
            messages.error(request, 'No se puede preliquidar una remisión cancelada.')
            return redirect('core:remision_list')
        
        # Obtener todos los detalles de la remisión
        detalles = self.object.detalles.all()
        
        # Procesar cada detalle
        from django.utils import timezone
        
        for detalle in detalles:
            # Obtener los datos del formulario para este detalle
            kgs_liquidados = request.POST.get(f'kgs_liquidados_{detalle.pk}', 0)
            kgs_merma = request.POST.get(f'kgs_merma_{detalle.pk}', 0)
            precio = request.POST.get(f'precio_{detalle.pk}', 0)
            importe_liquidado = request.POST.get(f'importe_liquidado_{detalle.pk}', 0)
            
            # Convertir a decimal y actualizar
            try:
                detalle.kgs_liquidados = round(float(kgs_liquidados or 0), 2)
                detalle.kgs_merma = round(float(kgs_merma or 0), 2)
                detalle.precio = round(float(precio or 0), 2)
                detalle.importe_liquidado = round(float(importe_liquidado or 0), 2)
                
                # Guardar información de auditoría de liquidación
                detalle.usuario_liquidacion = request.user
                detalle.fecha_liquidacion = timezone.now()
                
                detalle.save()
            except (ValueError, TypeError):
                messages.error(request, f'Error en los datos del detalle {detalle.cultivo.nombre}.')
                return self.form_invalid(None)
        
        messages.success(request, f'Remisión "{self.object.ciclo} - {self.object.folio:06d}" preliquidada exitosamente.')
        return redirect('core:remision_list')
    
    def esta_liquidada(self, remision):
        """Determinar si una remisión está preliquidada basándose en los campos de liquidación
        Y si tiene información de auditoría (usuario_liquidacion y fecha_liquidacion)
        """
        detalles = remision.detalles.all()
        if not detalles.exists():
            return False
        
        # Una remisión está preliquidada si al menos un detalle tiene valores de liquidación
        # Y tiene información de auditoría (usuario_liquidacion y fecha_liquidacion)
        for detalle in detalles:
            if ((detalle.kgs_liquidados > 0 or 
                 detalle.kgs_merma > 0 or 
                 detalle.precio > 0 or 
                 detalle.importe_liquidado > 0) and
                detalle.usuario_liquidacion is not None and
                detalle.fecha_liquidacion is not None):
                return True
        return False
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error en el formulario de liquidación.')
        return super().form_invalid(form)


class RemisionUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar remisiones"""
    model = Remision
    form_class = RemisionForm
    template_name = 'core/remision_form.html'
    success_url = reverse_lazy('core:remision_list')
    
    def get(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de permitir la edición"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede editar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de procesar la actualización"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede editar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que modifica el registro
            form.instance.usuario_modificacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Remisión "{form.instance.ciclo} - {form.instance.folio:06d}" actualizada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar remisión: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Remisión: {self.object.ciclo} - {self.object.folio:06d}'
        return context


class RemisionDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar detalles de una remisión"""
    template_name = 'core/remision_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remision = get_object_or_404(Remision, pk=kwargs['pk'])
        context['remision'] = remision
        context['detalles'] = remision.detalles.all()
        context['title'] = f'Remisión: {remision.ciclo} - {remision.folio:06d}'
        return context


class RemisionImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir formato de remisión"""
    template_name = 'core/remision_imprimir.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remision = get_object_or_404(Remision, pk=kwargs['pk'])
        context['remision'] = remision
        context['detalles'] = remision.detalles.all()
        return context


class RemisionDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar remisiones"""
    model = Remision
    template_name = 'core/remision_confirm_delete.html'
    success_url = reverse_lazy('core:remision_list')
    
    def get(self, request, *args, **kwargs):
        """Verificar que la remisión no esté cancelada antes de permitir la eliminación"""
        self.object = self.get_object()
        
        if self.object.cancelada:
            messages.error(request, 'No se puede eliminar una remisión cancelada.')
            return redirect('core:remision_list')
        
        return super().get(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            remision = self.get_object()
            
            # Verificar que la remisión no esté cancelada
            if remision.cancelada:
                messages.error(request, 'No se puede eliminar una remisión cancelada.')
                return redirect('core:remision_list')
            
            remision_str = f"{remision.ciclo} - {remision.folio:06d}"
            
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Remisión "{remision_str}" eliminada exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar remisión: {str(e)}')
            return redirect('core:remision_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Remisión: {self.object.ciclo} - {self.object.folio:06d}'
        return context


# ===========================
# VISTAS PARA CRUD DE DETALLES DE REMISIONES
# ===========================

class RemisionDetalleCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear detalles de remisiones"""
    model = RemisionDetalle
    form_class = RemisionDetalleForm
    template_name = 'core/remision_detalle_form.html'
    
    def get_success_url(self):
        return reverse_lazy('core:remision_detail', kwargs={'pk': self.kwargs['remision_id']})
    
    def form_valid(self, form):
        try:
            # Asignar la remisión y el usuario que crea el registro
            remision = get_object_or_404(Remision, pk=self.kwargs['remision_id'])
            form.instance.remision = remision
            form.instance.usuario_creacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Detalle de remisión creado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al crear detalle de remisión: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remision = get_object_or_404(Remision, pk=self.kwargs['remision_id'])
        context['remision'] = remision
        context['title'] = f'Nuevo Detalle - Remisión: {remision.ciclo} - {remision.folio:06d}'
        return context


class RemisionDetalleUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar detalles de remisiones"""
    model = RemisionDetalle
    form_class = RemisionDetalleForm
    template_name = 'core/remision_detalle_form.html'
    
    def get_success_url(self):
        return reverse_lazy('core:remision_detail', kwargs={'pk': self.object.remision.pk})
    
    def form_valid(self, form):
        try:
            # Asignar el usuario que modifica el registro
            form.instance.usuario_modificacion = self.request.user
            
            response = super().form_valid(form)
            messages.success(self.request, f'Detalle de remisión actualizado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al actualizar detalle de remisión: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        error_count = len(form.errors)
        if error_count == 1:
            messages.error(self.request, 'Hay 1 error en el formulario. Por favor, corríjalo.')
        else:
            messages.error(self.request, f'Hay {error_count} errores en el formulario. Por favor, corríjalos.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remision'] = self.object.remision
        context['title'] = f'Editar Detalle - Remisión: {self.object.remision.ciclo} - {self.object.remision.folio:06d}'
        return context


class RemisionDetalleDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar detalles de remisiones"""
    model = RemisionDetalle
    template_name = 'core/remision_detalle_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('core:remision_detail', kwargs={'pk': self.object.remision.pk})
    
    def delete(self, request, *args, **kwargs):
        try:
            detalle = self.get_object()
            remision_str = f"{detalle.remision.ciclo} - {detalle.remision.folio:06d}"
            
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f'Detalle de remisión eliminado exitosamente.')
            return response
        except Exception as e:
            messages.error(self.request, f'Error al eliminar detalle de remisión: {str(e)}')
            return redirect('core:remision_detail', pk=self.object.remision.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remision'] = self.object.remision
        context['title'] = f'Eliminar Detalle - Remisión: {self.object.remision.ciclo} - {self.object.remision.folio:06d}'
        return context


@login_required
def cancelar_remision_ajax(request, pk):
    """Vista AJAX para cancelar una remisión"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Verificar que el usuario sea administrador
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tiene permisos para cancelar remisiones'}, status=403)
    
    try:
        remision = get_object_or_404(Remision, pk=pk)
        
        # Verificar que la remisión no esté ya cancelada
        if remision.cancelada:
            return JsonResponse({'error': 'Esta remisión ya está cancelada'}, status=400)
        
        # Procesar el formulario
        form = RemisionCancelacionForm(request.POST)
        
        if form.is_valid():
            # Actualizar la remisión con los datos de cancelación
            from django.utils import timezone
            
            remision.cancelada = True
            remision.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
            remision.folio_sustituto = form.cleaned_data['folio_sustituto'] or None
            remision.usuario_cancelacion = request.user
            remision.fecha_cancelacion = timezone.now()
            remision.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Remisión "{remision.ciclo} - {remision.folio:06d}" cancelada exitosamente.',
                'remision_id': remision.pk,
                'estado': 'Cancelada'
            })
        else:
            # Devolver errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if error_list else ''
            
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CobranzaListView(LoginRequiredMixin, ListView):
    """Vista para listar remisiones preliquidadas agrupadas por cliente para cobranza"""
    model = Remision
    template_name = 'core/cobranza_list.html'
    context_object_name = 'remisiones_agrupadas'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtener remisiones preliquidadas agrupadas por cliente con filtros"""
        # Obtener parámetros de búsqueda
        busqueda = self.request.GET.get('busqueda', '')
        cliente_id = self.request.GET.get('cliente', '')
        estado_facturacion = self.request.GET.get('estado_facturacion', '')
        estado_pago = self.request.GET.get('estado_pago', '')
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        
        # Filtrar solo remisiones preliquidadas y no canceladas
        remisiones = Remision.objects.filter(
            cancelada=False
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtros
        if busqueda:
            remisiones = remisiones.filter(
                Q(ciclo__icontains=busqueda) |
                Q(folio__icontains=busqueda) |
                Q(cliente__razon_social__icontains=busqueda)
            )
        
        if cliente_id:
            remisiones = remisiones.filter(cliente_id=cliente_id)
        
        if estado_facturacion == 'pendiente':
            remisiones = remisiones.filter(facturado=False)
        elif estado_facturacion == 'facturado':
            remisiones = remisiones.filter(facturado=True)
        
        
        if fecha_desde:
            remisiones = remisiones.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones = remisiones.filter(fecha__lte=fecha_hasta)
        
        # Filtrar solo las que están preliquidadas
        remisiones_preliquidadas = []
        for remision in remisiones:
            if remision.esta_liquidada():
                # Aplicar filtro de estado de pago basado en saldo pendiente
                saldo_pendiente = remision.saldo_pendiente
                
                if estado_pago == 'pendiente':
                    # Mostrar solo remisiones con saldo pendiente (no pagadas completamente)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
                elif estado_pago == 'pagado':
                    # Mostrar solo remisiones con saldo cero (completamente pagadas)
                    if saldo_pendiente == 0:
                        remisiones_preliquidadas.append(remision)
                else:
                    # Sin filtro de estado de pago, mostrar solo las no pagadas (comportamiento por defecto)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
        
        # Agrupar por cliente
        clientes_dict = {}
        for remision in remisiones_preliquidadas:
            cliente = remision.cliente
            if cliente not in clientes_dict:
                clientes_dict[cliente] = []
            clientes_dict[cliente].append(remision)
        
        # Convertir a lista de tuplas (cliente, lista_remisiones)
        clientes_agrupados = []
        for cliente, remisiones_cliente in clientes_dict.items():
            # Ordenar remisiones por fecha descendente
            remisiones_cliente.sort(key=lambda x: x.fecha, reverse=True)
            clientes_agrupados.append((cliente, remisiones_cliente))
        
        # Ordenar por razón social del cliente
        clientes_agrupados.sort(key=lambda x: x[0].razon_social)
        
        return clientes_agrupados
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cobranza - Remisiones Preliquidadas'
        
        # Agregar formulario de búsqueda
        context['search_form'] = CobranzaSearchForm(self.request.GET)
        
        # Calcular totales por cliente y agregar a cada tupla
        remisiones_agrupadas_con_totales = []
        total_general = 0
        saldo_general = 0
        
        for cliente, remisiones in context['remisiones_agrupadas']:
            total_importe = 0
            saldo_cliente = 0
            remisiones_con_importe = []
            
            for remision in remisiones:
                # Calcular el importe total de esta remisión
                importe_remision = 0
                for detalle in remision.detalles.all():
                    importe_remision += detalle.importe_liquidado
                
                # Calcular el saldo pendiente de la remisión
                saldo_remision = remision.saldo_pendiente
                
                # Agregar el importe de la remisión al total del cliente
                total_importe += importe_remision
                saldo_cliente += saldo_remision
                
                # Crear una tupla con la remisión y su importe
                remisiones_con_importe.append((remision, importe_remision))
            
            # Agregar el total y saldo a la tupla
            remisiones_agrupadas_con_totales.append((cliente, remisiones_con_importe, total_importe, saldo_cliente))
            total_general += total_importe
            saldo_general += saldo_cliente
        
        context['remisiones_agrupadas'] = remisiones_agrupadas_con_totales
        context['total_general'] = total_general
        context['saldo_general'] = saldo_general
        
        return context


@login_required
def actualizar_estado_cobranza_ajax(request, pk):
    """Vista AJAX para actualizar el estado de facturado o pagado de una remisión"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        remision = get_object_or_404(Remision, pk=pk)
        
        # Verificar que la remisión esté preliquidada
        if not remision.esta_liquidada():
            return JsonResponse({
                'error': 'Solo se pueden actualizar remisiones preliquidadas'
            }, status=400)
        
        # Verificar que la remisión no esté cancelada
        if remision.cancelada:
            return JsonResponse({
                'error': 'No se puede actualizar una remisión cancelada'
            }, status=400)
        
        # Obtener la acción a realizar
        accion = request.POST.get('accion')
        
        if accion == 'facturado':
            # Marcar como facturado
            remision.facturado = True
            remision.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Remisión "{remision.ciclo} - {remision.folio:06d}" marcada como facturada.',
                'remision_id': remision.pk,
                'estado': 'Facturado'
            })
            
        elif accion == 'pagado':
            # Verificar que esté facturado antes de marcar como pagado
            if not remision.facturado:
                return JsonResponse({
                    'error': 'La remisión debe estar facturada antes de marcarla como pagada'
                }, status=400)
            
            # Marcar como pagado
            remision.pagado = True
            remision.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Remisión "{remision.ciclo} - {remision.folio:06d}" marcada como pagada.',
                'remision_id': remision.pk,
                'estado': 'Pagado'
            })
            
        else:
            return JsonResponse({
                'error': 'Acción no válida. Use "facturado" o "pagado"'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


class CobranzaImprimirView(LoginRequiredMixin, TemplateView):
    """Vista para imprimir el estado de cuenta de cobranza"""
    template_name = 'core/cobranza_imprimir.html'
    
    def get_queryset(self):
        """Obtener remisiones preliquidadas con los mismos filtros que la vista principal"""
        # Obtener parámetros de búsqueda (mismo código que CobranzaListView)
        busqueda = self.request.GET.get('busqueda', '')
        cliente_id = self.request.GET.get('cliente', '')
        estado_facturacion = self.request.GET.get('estado_facturacion', '')
        estado_pago = self.request.GET.get('estado_pago', '')
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        
        # Filtrar solo remisiones preliquidadas y no canceladas
        remisiones = Remision.objects.filter(
            cancelada=False
        ).select_related('cliente').prefetch_related('detalles')
        
        # Aplicar filtros (mismo código que CobranzaListView)
        if busqueda:
            remisiones = remisiones.filter(
                Q(ciclo__icontains=busqueda) |
                Q(folio__icontains=busqueda) |
                Q(cliente__razon_social__icontains=busqueda)
            )
        
        if cliente_id:
            remisiones = remisiones.filter(cliente_id=cliente_id)
        
        if estado_facturacion == 'pendiente':
            remisiones = remisiones.filter(facturado=False)
        elif estado_facturacion == 'facturado':
            remisiones = remisiones.filter(facturado=True)
        
        
        if fecha_desde:
            remisiones = remisiones.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            remisiones = remisiones.filter(fecha__lte=fecha_hasta)
        
        # Filtrar solo las que están preliquidadas
        remisiones_preliquidadas = []
        for remision in remisiones:
            if remision.esta_liquidada():
                # Aplicar filtro de estado de pago basado en saldo pendiente
                saldo_pendiente = remision.saldo_pendiente
                
                if estado_pago == 'pendiente':
                    # Mostrar solo remisiones con saldo pendiente (no pagadas completamente)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
                elif estado_pago == 'pagado':
                    # Mostrar solo remisiones con saldo cero (completamente pagadas)
                    if saldo_pendiente == 0:
                        remisiones_preliquidadas.append(remision)
                else:
                    # Sin filtro de estado de pago, mostrar solo las no pagadas (comportamiento por defecto)
                    if saldo_pendiente > 0:
                        remisiones_preliquidadas.append(remision)
        
        # Agrupar por cliente
        clientes_dict = {}
        for remision in remisiones_preliquidadas:
            cliente = remision.cliente
            if cliente not in clientes_dict:
                clientes_dict[cliente] = []
            clientes_dict[cliente].append(remision)
        
        # Convertir a lista de tuplas (cliente, lista_remisiones)
        clientes_agrupados = []
        for cliente, remisiones_cliente in clientes_dict.items():
            # Ordenar remisiones por fecha descendente
            remisiones_cliente.sort(key=lambda x: x.fecha, reverse=True)
            clientes_agrupados.append((cliente, remisiones_cliente))
        
        # Ordenar por razón social del cliente
        clientes_agrupados.sort(key=lambda x: x[0].razon_social)
        
        return clientes_agrupados
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Estado de Cuenta - Cobranza'
        
        # Obtener datos con filtros aplicados
        remisiones_agrupadas = self.get_queryset()
        
        # Calcular totales por cliente y agregar a cada tupla
        remisiones_agrupadas_con_totales = []
        total_general = 0
        saldo_general = 0
        
        for cliente, remisiones in remisiones_agrupadas:
            total_importe = 0
            saldo_cliente = 0
            remisiones_con_importe = []
            
            for remision in remisiones:
                # Calcular el importe total de esta remisión
                importe_remision = 0
                for detalle in remision.detalles.all():
                    importe_remision += detalle.importe_liquidado
                
                # Calcular el saldo pendiente de la remisión
                saldo_remision = remision.saldo_pendiente
                
                # Agregar el importe de la remisión al total del cliente
                total_importe += importe_remision
                saldo_cliente += saldo_remision
                
                # Crear una tupla con la remisión y su importe
                remisiones_con_importe.append((remision, importe_remision))
            
            # Agregar el total y saldo a la tupla
            remisiones_agrupadas_con_totales.append((cliente, remisiones_con_importe, total_importe, saldo_cliente))
            total_general += total_importe
            saldo_general += saldo_cliente
        
        context['remisiones_agrupadas'] = remisiones_agrupadas_con_totales
        context['total_general'] = total_general
        context['saldo_general'] = saldo_general
        
        # Información de filtros aplicados
        context['filtros_aplicados'] = {
            'busqueda': self.request.GET.get('busqueda', ''),
            'cliente_id': self.request.GET.get('cliente', ''),
            'estado_facturacion': self.request.GET.get('estado_facturacion', ''),
            'estado_pago': self.request.GET.get('estado_pago', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        return context


# ===========================
# VISTAS AJAX PARA CUENTAS BANCARIAS
# ===========================

@login_required
def agregar_cuenta_bancaria_ajax(request):
    """Vista AJAX para agregar una cuenta bancaria"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .models import CuentaBancaria
        
        # Obtener datos del formulario
        nombre_banco = request.POST.get('nombre_banco', '').strip()
        numero_cuenta = request.POST.get('numero_cuenta', '').strip()
        nombre_corto = request.POST.get('nombre_corto', '').strip()
        
        # Validar campos requeridos
        if not nombre_banco:
            return JsonResponse({'error': 'El nombre del banco es requerido'}, status=400)
        
        if not numero_cuenta:
            return JsonResponse({'error': 'El número de cuenta es requerido'}, status=400)
        
        if not nombre_corto:
            return JsonResponse({'error': 'El nombre corto es requerido'}, status=400)
        
        # Crear la cuenta bancaria
        cuenta = CuentaBancaria.objects.create(
            nombre_banco=nombre_banco,
            numero_cuenta=numero_cuenta,
            nombre_corto=nombre_corto,
            usuario_creacion=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cuenta bancaria agregada exitosamente',
            'cuenta': {
                'codigo': cuenta.codigo,
                'nombre_banco': cuenta.nombre_banco,
                'numero_cuenta': cuenta.numero_cuenta,
                'nombre_corto': cuenta.nombre_corto,
                'activo': cuenta.activo
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def listar_cuentas_bancarias_ajax(request):
    """Vista AJAX para listar cuentas bancarias"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .models import CuentaBancaria
        
        # Obtener todas las cuentas bancarias activas
        cuentas = CuentaBancaria.objects.filter(activo=True).order_by('nombre_corto')
        
        cuentas_data = []
        for cuenta in cuentas:
            cuentas_data.append({
                'codigo': cuenta.codigo,
                'nombre_banco': cuenta.nombre_banco,
                'numero_cuenta': cuenta.numero_cuenta,
                'nombre_corto': cuenta.nombre_corto,
                'activo': cuenta.activo
            })
        
        return JsonResponse({
            'success': True,
            'cuentas': cuentas_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_cuenta_bancaria_ajax(request, codigo):
    """Vista AJAX para eliminar una cuenta bancaria"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from .models import CuentaBancaria
        
        # Obtener la cuenta bancaria
        cuenta = get_object_or_404(CuentaBancaria, codigo=codigo)
        
        # Marcar como inactiva en lugar de eliminar
        cuenta.activo = False
        cuenta.usuario_modificacion = request.user
        cuenta.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cuenta bancaria eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
@login_required
def capturar_pago_ajax(request, remision_id):
    """Vista AJAX para capturar pagos de remisiones"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        remision = Remision.objects.get(pk=remision_id)
        
        # Obtener datos del formulario
        monto = float(request.POST.get('monto', 0))
        metodo_pago = request.POST.get('metodo_pago')
        cuenta_bancaria_id = request.POST.get('cuenta_bancaria')
        fecha_pago = request.POST.get('fecha_pago')
        referencia = request.POST.get('referencia', '')
        observaciones = request.POST.get('observaciones', '')
        
        # Validaciones
        if monto <= 0:
            return JsonResponse({'error': 'El monto debe ser mayor a 0'}, status=400)
        
        if not metodo_pago:
            return JsonResponse({'error': 'Debe seleccionar un método de pago'}, status=400)
        
        if metodo_pago in ['transferencia', 'cheque'] and not cuenta_bancaria_id:
            return JsonResponse({'error': 'Debe seleccionar una cuenta bancaria para transferencias y cheques'}, status=400)
        
        if not fecha_pago:
            return JsonResponse({'error': 'Debe seleccionar una fecha de pago'}, status=400)
        
        # Obtener cuenta bancaria si es necesaria
        cuenta_bancaria = None
        if cuenta_bancaria_id:
            try:
                cuenta_bancaria = CuentaBancaria.objects.get(pk=cuenta_bancaria_id, activo=True)
            except CuentaBancaria.DoesNotExist:
                return JsonResponse({'error': 'Cuenta bancaria no encontrada'}, status=400)
        
        # Crear el pago
        from datetime import datetime
        fecha_pago_obj = datetime.strptime(fecha_pago, '%Y-%m-%d').date()
        
        pago = PagoRemision.objects.create(
            remision=remision,
            cuenta_bancaria=cuenta_bancaria,
            metodo_pago=metodo_pago,
            monto=monto,
            fecha_pago=fecha_pago_obj,
            referencia=referencia,
            observaciones=observaciones,
            usuario_creacion=request.user
        )
        
        # Calcular el total pagado de la remisión
        total_pagado = PagoRemision.objects.filter(remision=remision, activo=True).aggregate(
            total=models.Sum('monto')
        )['total'] or 0
        
        # Calcular el total de la remisión (suma de detalles)
        total_remision = remision.detalles.aggregate(
            total=models.Sum('importe_liquidado')
        )['total'] or 0
        
        # Marcar como pagada solo si el total pagado es mayor o igual al total de la remisión
        if total_pagado >= total_remision:
            remision.pagado = True
            remision.fecha_pago = fecha_pago_obj
            remision.save()
        return JsonResponse({
            'success': True,
            'message': f'Pago de ${monto:,.2f} capturado correctamente',
            'pago_id': pago.codigo
        })
        
    except Remision.DoesNotExist:
        return JsonResponse({'error': 'Remisión no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Error al capturar el pago: {str(e)}'
        }, status=500)


@login_required
def reporte_pagos_view(request):
    """Vista para mostrar reporte de pagos agrupados por cuenta bancaria"""
    # Obtener parámetros de filtro
    cliente_id = request.GET.get('cliente_id') or request.GET.get('cliente')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    remision = request.GET.get('remision')
    cuenta_bancaria_id = request.GET.get('cuenta_bancaria')
    metodo_pago = request.GET.get('metodo_pago')
    
    # Obtener pagos
    pagos_query = PagoRemision.objects.filter(activo=True).select_related(
        'remision', 'cuenta_bancaria', 'remision__cliente'
    )
    
    # Aplicar filtros
    if cliente_id:
        pagos_query = pagos_query.filter(remision__cliente_id=cliente_id)
        cliente = Cliente.objects.get(pk=cliente_id)
        titulo = f"Reporte de Pagos - {cliente.razon_social}"
    else:
        cliente = None
        titulo = "Reporte General de Pagos"
    
    if fecha_desde:
        pagos_query = pagos_query.filter(fecha_pago__gte=fecha_desde)
    
    if fecha_hasta:
        pagos_query = pagos_query.filter(fecha_pago__lte=fecha_hasta)
    
    if remision:
        # Buscar por ciclo-folio
        if '-' in remision:
            try:
                ciclo, folio = remision.split('-', 1)
                pagos_query = pagos_query.filter(
                    remision__ciclo=ciclo,
                    remision__folio=int(folio)
                )
            except (ValueError, IndexError):
                pass  # Si no se puede parsear, no filtrar
    
    if cuenta_bancaria_id:
        if cuenta_bancaria_id == 'efectivo':
            pagos_query = pagos_query.filter(cuenta_bancaria__isnull=True)
        else:
            pagos_query = pagos_query.filter(cuenta_bancaria_id=cuenta_bancaria_id)
    
    if metodo_pago:
        pagos_query = pagos_query.filter(metodo_pago=metodo_pago)
    
    # Agrupar por cuenta bancaria
    pagos_por_cuenta = {}
    total_general = 0
    
    for pago in pagos_query:
        if pago.cuenta_bancaria:
            cuenta_key = pago.cuenta_bancaria.codigo
            cuenta_nombre = pago.cuenta_bancaria.nombre_corto
        else:
            cuenta_key = f'efectivo_{pago.metodo_pago}'
            cuenta_nombre = f'Efectivo ({pago.get_metodo_pago_display()})'
        
        if cuenta_key not in pagos_por_cuenta:
            pagos_por_cuenta[cuenta_key] = {
                'cuenta_nombre': cuenta_nombre,
                'pagos': [],
                'total': 0,
                'cantidad': 0
            }
        
        pagos_por_cuenta[cuenta_key]['pagos'].append(pago)
        pagos_por_cuenta[cuenta_key]['total'] += pago.monto
        pagos_por_cuenta[cuenta_key]['cantidad'] += 1
        total_general += pago.monto
    
    # Obtener datos para el modal de filtros
    clientes = Cliente.objects.all().order_by('razon_social')
    cuentas_bancarias = CuentaBancaria.objects.filter(activo=True).order_by('nombre_corto')
    
    context = {
        'titulo': titulo,
        'cliente': cliente,
        'pagos_por_cuenta': pagos_por_cuenta,
        'total_general': total_general,
        'fecha_reporte': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'clientes': clientes,
        'cuentas_bancarias': cuentas_bancarias,
    }
    
    return render(request, 'core/reporte_pagos.html', context)


# ==================== VISTAS DE PRESUPUESTOS ====================

class PresupuestoGastoListView(LoginRequiredMixin, ListView):
    """Vista para listar presupuestos de gastos"""
    model = PresupuestoGasto
    template_name = 'core/presupuesto_gasto_list.html'
    context_object_name = 'presupuestos'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtener presupuestos con filtros"""
        # Obtener parámetros de búsqueda
        busqueda = self.request.GET.get('busqueda', '')
        centro_costo_id = self.request.GET.get('centro_costo', '')
        clasificacion_gasto_id = self.request.GET.get('clasificacion_gasto', '')
        ciclo = self.request.GET.get('ciclo', '')
        
        # Filtrar solo presupuestos activos
        presupuestos = PresupuestoGasto.objects.filter(
            activo=True
        ).select_related('centro_costo', 'clasificacion_gasto', 'usuario_creacion')
        
        # Aplicar filtros
        if busqueda:
            presupuestos = presupuestos.filter(
                Q(centro_costo__descripcion__icontains=busqueda) |
                Q(clasificacion_gasto__descripcion__icontains=busqueda) |
                Q(ciclo__icontains=busqueda)
            )
        
        if centro_costo_id:
            presupuestos = presupuestos.filter(centro_costo_id=centro_costo_id)
        
        if clasificacion_gasto_id:
            presupuestos = presupuestos.filter(clasificacion_gasto_id=clasificacion_gasto_id)
        
        if ciclo:
            presupuestos = presupuestos.filter(ciclo__icontains=ciclo)
        
        return presupuestos.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Presupuestos de Gastos'
        
        # Agregar formulario de búsqueda
        context['search_form'] = PresupuestoGastoSearchForm(self.request.GET)
        
        # Obtener ciclo actual de la configuración
        try:
            configuracion = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = configuracion.ciclo_actual if configuracion else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


class PresupuestoGastoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear presupuestos de gastos"""
    model = PresupuestoGasto
    form_class = PresupuestoGastoForm
    template_name = 'core/presupuesto_gasto_form.html'
    success_url = reverse_lazy('core:presupuesto_gasto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Presupuesto de Gasto'
        
        # Obtener ciclo actual de la configuración
        try:
            configuracion = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = configuracion.ciclo_actual if configuracion else ''
        except:
            context['ciclo_actual'] = ''
        
        return context
    
    def form_valid(self, form):
        # Asignar el usuario actual y el ciclo actual
        form.instance.usuario_creacion = self.request.user
        
        # Obtener ciclo actual de la configuración
        try:
            configuracion = ConfiguracionSistema.objects.first()
            if configuracion and configuracion.ciclo_actual:
                form.instance.ciclo = configuracion.ciclo_actual
        except:
            pass
        
        return super().form_valid(form)


class PresupuestoGastoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar presupuestos de gastos"""
    model = PresupuestoGasto
    form_class = PresupuestoGastoForm
    template_name = 'core/presupuesto_gasto_form.html'
    success_url = reverse_lazy('core:presupuesto_gasto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Presupuesto de Gasto'
        return context
    
    def form_valid(self, form):
        # Asignar el usuario de modificación
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)


class PresupuestoGastoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar presupuestos de gastos"""
    model = PresupuestoGasto
    template_name = 'core/presupuesto_gasto_confirm_delete.html'
    success_url = reverse_lazy('core:presupuesto_gasto_list')
    
    def delete(self, request, *args, **kwargs):
        # En lugar de eliminar, marcar como inactivo
        self.object = self.get_object()
        self.object.activo = False
        self.object.usuario_modificacion = request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


@login_required
def presupuesto_gasto_ajax(request, pk):
    """Vista AJAX para obtener datos de un presupuesto específico"""
    try:
        presupuesto = PresupuestoGasto.objects.get(pk=pk, activo=True)
        data = {
            'codigo': presupuesto.codigo,
            'centro_costo': presupuesto.centro_costo.descripcion,
            'clasificacion_gasto': presupuesto.clasificacion_gasto.descripcion,
            'ciclo': presupuesto.ciclo,
            'importe': float(presupuesto.importe),
            'observaciones': presupuesto.observaciones or '',
            'fecha_creacion': presupuesto.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'usuario_creacion': presupuesto.usuario_creacion.get_full_name() or presupuesto.usuario_creacion.username
        }
        return JsonResponse(data)
    except PresupuestoGasto.DoesNotExist:
        return JsonResponse({'error': 'Presupuesto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===========================
# VISTAS PARA PRESUPUESTOS (NUEVA ESTRUCTURA)
# ===========================

class PresupuestoListView(LoginRequiredMixin, ListView):
    """Vista para listar presupuestos"""
    model = Presupuesto
    template_name = 'core/presupuesto_list.html'
    context_object_name = 'presupuestos'
    paginate_by = 20
    
    def get_queryset(self):
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else ''
        except:
            ciclo_actual = ''
        
        # Filtrar por ciclo actual si está configurado
        if ciclo_actual:
            queryset = Presupuesto.objects.filter(activo=True, ciclo=ciclo_actual).select_related('centro_costo', 'usuario_creacion')
        else:
            queryset = Presupuesto.objects.filter(activo=True).select_related('centro_costo', 'usuario_creacion')
        
        # Aplicar filtros de búsqueda
        busqueda = self.request.GET.get('busqueda', '')
        centro_costo_id = self.request.GET.get('centro_costo', '')
        ciclo = self.request.GET.get('ciclo', '')
        
        if busqueda:
            queryset = queryset.filter(
                Q(centro_costo__descripcion__icontains=busqueda) |
                Q(ciclo__icontains=busqueda) |
                Q(observaciones__icontains=busqueda)
            )
        
        if centro_costo_id:
            queryset = queryset.filter(centro_costo_id=centro_costo_id)
        
        if ciclo:
            queryset = queryset.filter(ciclo__icontains=ciclo)
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PresupuestoSearchForm(self.request.GET)
        context['centros_costo'] = CentroCosto.objects.filter(activo=True)
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


class PresupuestoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear presupuestos"""
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = 'core/presupuesto_form.html'
    success_url = reverse_lazy('core:presupuesto_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario sea administrador
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para crear presupuestos.')
            return HttpResponseRedirect(reverse_lazy('core:presupuesto_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Inicializar el formulario con el ciclo actual"""
        initial = super().get_initial()
        try:
            config = ConfiguracionSistema.objects.first()
            initial['ciclo'] = config.ciclo_actual if config else '2025-2026'
        except:
            initial['ciclo'] = '2025-2026'
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else 'No definido'
        except:
            context['ciclo_actual'] = 'No definido'
        
        # Obtener clasificaciones de gastos para el modal
        context['clasificaciones_gastos'] = ClasificacionGasto.objects.filter(activo=True)
        
        return context
    
    def form_valid(self, form):
        # Establecer el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            form.instance.ciclo = config.ciclo_actual if config else '2025-2026'
        except:
            form.instance.ciclo = '2025-2026'
        
        # Establecer el usuario de creación
        form.instance.usuario_creacion = self.request.user
        
        # Guardar el presupuesto primero
        response = super().form_valid(form)
        
        # Crear los detalles temporales si existen
        detalles_temporales = self.request.POST.get('detalles_temporales')
        if detalles_temporales:
            try:
                import json
                detalles_data = json.loads(detalles_temporales)
                
                for detalle_data in detalles_data:
                    clasificacion_gasto = ClasificacionGasto.objects.get(
                        codigo=detalle_data['clasificacion_gasto']['codigo']
                    )
                    
                    PresupuestoDetalle.objects.create(
                        presupuesto=form.instance,
                        clasificacion_gasto=clasificacion_gasto,
                        importe=detalle_data['importe'],
                        usuario_creacion=self.request.user
                    )
            except Exception as e:
                # Si hay error al crear detalles, agregar mensaje de error
                messages.error(self.request, f'Error al crear algunos detalles: {str(e)}')
        
        return response
    
    def post(self, request, *args, **kwargs):
        # Manejar AJAX para agregar/eliminar detalles
        if request.headers.get('Content-Type') == 'application/json' or 'action' in request.POST:
            action = request.POST.get('action')
            
            if action == 'add_detalle':
                return self.add_detalle(request)
            elif action == 'delete_detalle':
                return self.delete_detalle(request)
        
        return super().post(request, *args, **kwargs)
    
    def add_detalle(self, request):
        """Agregar un detalle al presupuesto"""
        try:
            presupuesto_id = request.POST.get('presupuesto_id')
            clasificacion_gasto_id = request.POST.get('clasificacion_gasto')
            importe = request.POST.get('importe')
            
            if not all([presupuesto_id, clasificacion_gasto_id, importe]):
                return JsonResponse({'success': False, 'message': 'Faltan datos requeridos'})
            
            presupuesto = Presupuesto.objects.get(pk=presupuesto_id)
            clasificacion_gasto = ClasificacionGasto.objects.get(pk=clasificacion_gasto_id)
            
            detalle = PresupuestoDetalle.objects.create(
                presupuesto=presupuesto,
                clasificacion_gasto=clasificacion_gasto,
                importe=importe,
                usuario_creacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Detalle agregado correctamente',
                'detalle': {
                    'id': detalle.codigo,
                    'clasificacion': detalle.clasificacion_gasto.descripcion,
                    'importe': float(detalle.importe)
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    def delete_detalle(self, request):
        """Eliminar un detalle del presupuesto"""
        try:
            detalle_id = request.POST.get('detalle_id')
            detalle = PresupuestoDetalle.objects.get(pk=detalle_id)
            detalle.delete()
            
            return JsonResponse({'success': True, 'message': 'Detalle eliminado correctamente'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class PresupuestoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar presupuestos"""
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = 'core/presupuesto_form.html'
    success_url = reverse_lazy('core:presupuesto_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario sea administrador
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para editar presupuestos.')
            return HttpResponseRedirect(reverse_lazy('core:presupuesto_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Inicializar el formulario con el ciclo actual"""
        initial = super().get_initial()
        try:
            config = ConfiguracionSistema.objects.first()
            initial['ciclo'] = config.ciclo_actual if config else '2025-2026'
        except:
            initial['ciclo'] = '2025-2026'
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else 'No definido'
        except:
            context['ciclo_actual'] = 'No definido'
        
        # Obtener clasificaciones de gastos para el modal
        context['clasificaciones_gastos'] = ClasificacionGasto.objects.filter(activo=True)
        
        return context
    
    def form_valid(self, form):
        # Establecer el usuario de modificación
        form.instance.usuario_modificacion = self.request.user
        
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        # Manejar AJAX para agregar/eliminar detalles
        if request.headers.get('Content-Type') == 'application/json' or 'action' in request.POST:
            action = request.POST.get('action')
            
            if action == 'add_detalle':
                return self.add_detalle(request)
            elif action == 'delete_detalle':
                return self.delete_detalle(request)
        
        return super().post(request, *args, **kwargs)
    
    def add_detalle(self, request):
        """Agregar un detalle al presupuesto"""
        try:
            presupuesto_id = self.get_object().codigo
            clasificacion_gasto_id = request.POST.get('clasificacion_gasto')
            importe = request.POST.get('importe')
            
            if not all([presupuesto_id, clasificacion_gasto_id, importe]):
                return JsonResponse({'success': False, 'message': 'Faltan datos requeridos'})
            
            presupuesto = Presupuesto.objects.get(pk=presupuesto_id)
            clasificacion_gasto = ClasificacionGasto.objects.get(pk=clasificacion_gasto_id)
            
            detalle = PresupuestoDetalle.objects.create(
                presupuesto=presupuesto,
                clasificacion_gasto=clasificacion_gasto,
                importe=importe,
                usuario_creacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Detalle agregado correctamente',
                'detalle': {
                    'id': detalle.codigo,
                    'clasificacion': detalle.clasificacion_gasto.descripcion,
                    'importe': float(detalle.importe)
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    def delete_detalle(self, request):
        """Eliminar un detalle del presupuesto"""
        try:
            detalle_id = request.POST.get('detalle_id')
            detalle = PresupuestoDetalle.objects.get(pk=detalle_id)
            detalle.delete()
            
            return JsonResponse({'success': True, 'message': 'Detalle eliminado correctamente'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class PresupuestoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar presupuestos"""
    model = Presupuesto
    template_name = 'core/presupuesto_confirm_delete.html'
    success_url = reverse_lazy('core:presupuesto_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario sea administrador
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para eliminar presupuestos.')
            return HttpResponseRedirect(reverse_lazy('core:presupuesto_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Eliminar lógicamente el presupuesto"""
        self.object = self.get_object()
        self.object.activo = False
        self.object.usuario_modificacion = request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


def clasificaciones_gastos_ajax(request):
    """Vista AJAX para obtener clasificaciones de gastos activas"""
    try:
        clasificaciones = ClasificacionGasto.objects.filter(activo=True).values('codigo', 'descripcion')
        data = {
            'success': True,
            'clasificaciones': list(clasificaciones)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def presupuesto_detalle_ajax(request, pk):
    """Vista AJAX para agregar un detalle a un presupuesto existente"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            # Obtener el presupuesto
            presupuesto = get_object_or_404(Presupuesto, codigo=pk, activo=True)
            
            # Obtener la clasificación de gasto
            clasificacion_gasto = get_object_or_404(ClasificacionGasto, codigo=data['clasificacion_gasto']['codigo'], activo=True)
            
            # Crear el detalle
            detalle = PresupuestoDetalle.objects.create(
                presupuesto=presupuesto,
                clasificacion_gasto=clasificacion_gasto,
                importe=data['importe'],
                usuario_creacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Detalle agregado correctamente',
                'detalle_codigo': detalle.codigo
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


class PresupuestoDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar los detalles de un presupuesto"""
    template_name = 'core/presupuesto_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, codigo=kwargs['pk'], activo=True)
        context['presupuesto'] = presupuesto
        context['detalles'] = presupuesto.detalles.filter(activo=True).order_by('clasificacion_gasto__descripcion')
        
        # Calcular gastos por clasificación
        gastos_por_clasificacion = {}
        total_gastado = 0
        
        # Obtener todos los gastos del presupuesto
        gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True)
        
        for gasto in gastos:
            for detalle_gasto in gasto.detalles.filter(activo=True):
                clasificacion_id = detalle_gasto.clasificacion_gasto.codigo
                if clasificacion_id not in gastos_por_clasificacion:
                    gastos_por_clasificacion[clasificacion_id] = 0
                gastos_por_clasificacion[clasificacion_id] += float(detalle_gasto.importe)
                total_gastado += float(detalle_gasto.importe)
        
        context['gastos_por_clasificacion'] = gastos_por_clasificacion
        context['total_gastado'] = total_gastado
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context


# Vistas para Gastos
class GastoListView(LoginRequiredMixin, ListView):
    """Vista para listar gastos"""
    model = Gasto
    template_name = 'core/gasto_list.html'
    context_object_name = 'gastos'
    paginate_by = 20

    def get_queryset(self):
        queryset = Gasto.objects.filter(activo=True).select_related(
            'presupuesto', 'presupuesto__centro_costo', 'usuario_creacion'
        ).order_by('-fecha_creacion')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Gastos'
        return context


class GastoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear gastos con modal master-detail"""
    model = Gasto
    form_class = GastoForm
    template_name = 'core/gasto_form.html'
    success_url = reverse_lazy('core:gasto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        return context

    def post(self, request, *args, **kwargs):
        # Si es una petición AJAX desde el modal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'detalles_temporales' in request.POST:
            return self.handle_ajax_request(request)
        return super().post(request, *args, **kwargs)

    def handle_ajax_request(self, request):
        """Manejar petición AJAX para crear gasto desde modal"""
        try:
            # Crear el gasto principal
            presupuesto = Presupuesto.objects.get(codigo=request.POST.get('presupuesto'))
            gasto = Gasto.objects.create(
                presupuesto=presupuesto,
                ciclo=request.POST.get('ciclo'),
                fecha_gasto=request.POST.get('fecha_gasto'),
                observaciones=request.POST.get('observaciones', ''),
                activo=True,
                usuario_creacion=request.user
            )
            
            # Procesar detalles temporales
            detalles_temporales = request.POST.get('detalles_temporales')
            if detalles_temporales:
                import json
                detalles_data = json.loads(detalles_temporales)
                for detalle_data in detalles_data:
                    proveedor = Proveedor.objects.get(codigo=detalle_data['proveedor']['codigo'])
                    clasificacion_gasto = ClasificacionGasto.objects.get(
                        codigo=detalle_data['clasificacion_gasto']['codigo']
                    )
                    GastoDetalle.objects.create(
                        gasto=gasto,
                        proveedor=proveedor,
                        factura=detalle_data['factura'],
                        clasificacion_gasto=clasificacion_gasto,
                        concepto=detalle_data['concepto'],
                        importe=detalle_data['importe'],
                        usuario_creacion=request.user
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Gasto creado correctamente',
                'gasto_id': gasto.codigo
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        form.instance.ciclo = form.cleaned_data['ciclo']
        response = super().form_valid(form)
        
        # Procesar detalles temporales si existen
        detalles_temporales = self.request.POST.get('detalles_temporales')
        if detalles_temporales:
            try:
                import json
                detalles_data = json.loads(detalles_temporales)
                for detalle_data in detalles_data:
                    proveedor = Proveedor.objects.get(codigo=detalle_data['proveedor']['codigo'])
                    clasificacion_gasto = ClasificacionGasto.objects.get(
                        codigo=detalle_data['clasificacion_gasto']['codigo']
                    )
                    GastoDetalle.objects.create(
                        gasto=form.instance,
                        proveedor=proveedor,
                        factura=detalle_data['factura'],
                        clasificacion_gasto=clasificacion_gasto,
                        concepto=detalle_data['concepto'],
                        importe=detalle_data['importe'],
                        usuario_creacion=self.request.user
                    )
            except Exception as e:
                messages.error(self.request, f'Error al crear algunos detalles: {str(e)}')
        
        return response


class GastoDetailView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar los detalles de un gasto"""
    template_name = 'core/gasto_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gasto = get_object_or_404(Gasto, codigo=kwargs['pk'], activo=True)
        context['gasto'] = gasto
        context['detalles'] = gasto.detalles.filter(activo=True).order_by('proveedor__razon_social')
        return context


class GastoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar gastos"""
    model = Gasto
    form_class = GastoForm
    template_name = 'core/gasto_form.html'
    success_url = reverse_lazy('core:gasto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        return context

    def form_valid(self, form):
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)


class GastoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar gastos (inactivar)"""
    model = Gasto
    template_name = 'core/gasto_confirm_delete.html'
    success_url = reverse_lazy('core:gasto_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.activo = False
        self.object.usuario_modificacion = request.user
        self.object.save()
        messages.success(request, 'Gasto eliminado correctamente.')
        return HttpResponseRedirect(self.get_success_url())


# Vistas AJAX para gastos
def proveedores_ajax(request):
    """Vista AJAX para obtener proveedores activos"""
    try:
        proveedores = Proveedor.objects.filter(activo=True).values('codigo', 'nombre')
        data = {
            'success': True,
            'proveedores': list(proveedores)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def clasificaciones_gastos_presupuesto_ajax(request, presupuesto_id):
    """Vista AJAX para obtener clasificaciones de gastos de un presupuesto específico"""
    try:
        presupuesto = get_object_or_404(Presupuesto, codigo=presupuesto_id, activo=True)
        clasificaciones_ids = presupuesto.detalles.filter(activo=True).values_list('clasificacion_gasto_id', flat=True)
        clasificaciones = ClasificacionGasto.objects.filter(
            codigo__in=clasificaciones_ids,
            activo=True
        ).values('codigo', 'descripcion')
        
        data = {
            'success': True,
            'clasificaciones': list(clasificaciones)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


class PresupuestoGastoFormView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar el formulario de captura de gastos para un presupuesto específico"""
    template_name = 'core/presupuesto_gasto_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, codigo=kwargs['pk'], activo=True)
        context['presupuesto'] = presupuesto
        
        # Calcular gastos por clasificación
        gastos_por_clasificacion = {}
        total_gastado = 0
        
        # Obtener todos los gastos del presupuesto
        gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True)
        
        for gasto in gastos:
            for detalle_gasto in gasto.detalles.filter(activo=True):
                clasificacion_id = detalle_gasto.clasificacion_gasto.codigo
                if clasificacion_id not in gastos_por_clasificacion:
                    gastos_por_clasificacion[clasificacion_id] = 0
                gastos_por_clasificacion[clasificacion_id] += float(detalle_gasto.importe)
                total_gastado += float(detalle_gasto.importe)
        
        context['gastos_por_clasificacion'] = gastos_por_clasificacion
        context['total_gastado'] = total_gastado
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context
class PresupuestoGastosReporteView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar el reporte de gastos de un presupuesto específico"""
    template_name = 'core/presupuesto_gastos_reporte.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, codigo=kwargs['pk'], activo=True)
        context['presupuesto'] = presupuesto
        
        # Obtener todos los gastos del presupuesto agrupados por clasificación
        gastos = Gasto.objects.filter(presupuesto=presupuesto, activo=True).prefetch_related('detalles__proveedor', 'detalles__clasificacion_gasto')
        
        # Agrupar gastos por clasificación
        gastos_por_clasificacion = {}
        total_gastado = 0
        
        for gasto in gastos:
            for detalle in gasto.detalles.filter(activo=True):
                clasificacion = detalle.clasificacion_gasto
                if clasificacion.codigo not in gastos_por_clasificacion:
                    gastos_por_clasificacion[clasificacion.codigo] = {
                        'clasificacion': clasificacion,
                        'detalles': [],
                        'subtotal': 0
                    }
                
                detalle_info = {
                    'gasto': gasto,
                    'proveedor': detalle.proveedor,
                    'factura': detalle.factura,
                    'concepto': detalle.concepto,
                    'importe': detalle.importe,
                    'fecha_gasto': gasto.fecha_gasto
                }
                
                gastos_por_clasificacion[clasificacion.codigo]['detalles'].append(detalle_info)
                gastos_por_clasificacion[clasificacion.codigo]['subtotal'] += float(detalle.importe)
                total_gastado += float(detalle.importe)
        
        # Ordenar por descripción de clasificación
        gastos_ordenados = sorted(gastos_por_clasificacion.values(), key=lambda x: x['clasificacion'].descripcion)
        
        context['gastos_por_clasificacion'] = gastos_ordenados
        context['total_gastado'] = total_gastado
        
        # Obtener el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            context['ciclo_actual'] = config.ciclo_actual if config else ''
        except:
            context['ciclo_actual'] = ''
        
        return context
