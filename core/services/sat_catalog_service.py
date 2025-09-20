import requests
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

class SATCatalogService:
    """
    Servicio para la gestión de catálogos SAT.
    Incluye descarga, actualización y validación de catálogos.
    """
    
    # URLs base de los catálogos SAT
    BASE_URL = "https://www.sat.gob.mx"
    CATALOGS_URL = f"{BASE_URL}/esquemas/ContabilidadE/1_3/CatalogosConVentas"
    # URL alternativa para catálogos
    CATALOGS_URL_ALT = f"{BASE_URL}/esquemas/ContabilidadE/1_3/CatalogosConVentas"
    
    # Mapeo de catálogos a sus archivos
    CATALOG_FILES = {
        'regimenes': 'c_RegimenFiscal',
        'usos-cfdi': 'c_UsoCFDI',
        'formas-pago': 'c_FormaPago',
        'metodos-pago': 'c_MetodoPago',
        'monedas': 'c_Moneda',
        'tipos-comprobante': 'c_TipoDeComprobante',
        'objeto-impuesto': 'c_ObjetoImp',
        'exportacion': 'c_TipoExportacion',
        'tipos-relacion': 'c_TipoRelacion',
        'impuestos': 'c_Impuesto',
        'tipos-factor': 'c_TipoFactor',
        'tipos-traslado': 'c_TipoTraslado',
        'tipos-retencion': 'c_TipoRetencion',
        'tipos-otro-pago': 'c_TipoOtroPago',
        'tipos-horas-extra': 'c_TipoHoras',
        'tipos-percepciones': 'c_TipoPercepcion',
        'tipos-deducciones': 'c_TipoDeduccion',
        'tipos-otras-obligaciones': 'c_TipoOtrasObligaciones',
        'tipos-jornadas': 'c_TipoJornada',
        'tipos-regimenes': 'c_TipoRegimen',
        'tipos-contratos': 'c_TipoContrato',
        'tipos-terminos': 'c_TipoTermino',
        'tipos-jornadas-trabajo': 'c_TipoJornadaTrabajo',
        'tipos-riesgo': 'c_TipoRiesgo',
        'tipos-percepciones-nomina': 'c_TipoPercepcionNomina',
        'tipos-deducciones-nomina': 'c_TipoDeduccionNomina',
        'tipos-otras-percepciones': 'c_TipoOtraPercepcion',
        'tipos-otras-deducciones': 'c_TipoOtraDeduccion',
        'tipos-horas-extra-nomina': 'c_TipoHorasExtra',
        'tipos-incapacidades': 'c_TipoIncapacidad',
        'tipos-deducciones-otras': 'c_TipoDeduccionOtra',
        'tipos-percepciones-otras': 'c_TipoPercepcionOtra',
        'tipos-deducciones-otras-nomina': 'c_TipoDeduccionOtraNomina',
        'tipos-percepciones-otras-nomina': 'c_TipoPercepcionOtraNomina',
    }
    
    @staticmethod
    def obtener_catalogo(nombre_catalogo: str, usar_cache: bool = True) -> dict:
        """
        Obtiene un catálogo específico del SAT.
        """
        cache_key = f"sat_catalog_{nombre_catalogo}"
        
        if usar_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Catálogo {nombre_catalogo} obtenido desde cache")
                return cached_data
        
        try:
            if nombre_catalogo not in SATCatalogService.CATALOG_FILES:
                raise ValueError(f"Catálogo '{nombre_catalogo}' no soportado")
            
            archivo = SATCatalogService.CATALOG_FILES[nombre_catalogo]
            url = f"{SATCatalogService.CATALOGS_URL}/{archivo}.xml"
            
            logger.info(f"Descargando catálogo {nombre_catalogo} desde {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parsear XML (simplificado, en producción usar lxml)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            catalogo_data = {
                'nombre': nombre_catalogo,
                'archivo': archivo,
                'fecha_descarga': timezone.now().isoformat(),
                'registros': []
            }
            
            # Extraer registros del XML
            for registro in root.findall('.//{http://www.sat.gob.mx/sitio_internet/cfd/catalogos}c_RegimenFiscal'):
                catalogo_data['registros'].append({
                    'codigo': registro.get('c_RegimenFiscal'),
                    'descripcion': registro.get('Descripcion'),
                    'vigencia_desde': registro.get('VigenciaDesde'),
                    'vigencia_hasta': registro.get('VigenciaHasta')
                })
            
            # Cachear por 24 horas
            cache.set(cache_key, catalogo_data, 86400)
            
            logger.info(f"Catálogo {nombre_catalogo} descargado exitosamente: {len(catalogo_data['registros'])} registros")
            return catalogo_data
            
        except requests.RequestException as e:
            logger.error(f"Error descargando catálogo {nombre_catalogo}: {e}")
            raise ConnectionError(f"Error de conexión al descargar catálogo {nombre_catalogo}: {e}")
        except ET.ParseError as e:
            logger.error(f"Error parseando XML del catálogo {nombre_catalogo}: {e}")
            raise ValueError(f"Error parseando catálogo {nombre_catalogo}: {e}")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo catálogo {nombre_catalogo}: {e}")
            raise
    
    @staticmethod
    def actualizar_catalogo(nombre_catalogo: str, forzar: bool = False) -> dict:
        """
        Actualiza un catálogo específico.
        """
        try:
            # Verificar si necesita actualización
            if not forzar:
                cache_key = f"sat_catalog_{nombre_catalogo}"
                cached_data = cache.get(cache_key)
                if cached_data:
                    # Verificar si tiene menos de 7 días
                    fecha_descarga = datetime.fromisoformat(cached_data['fecha_descarga'].replace('Z', '+00:00'))
                    if (timezone.now() - fecha_descarga).days < 7:
                        return {
                            'actualizado': False,
                            'mensaje': f"Catálogo {nombre_catalogo} ya está actualizado (menos de 7 días)"
                        }
            
            # Descargar catálogo
            catalogo_data = SATCatalogService.obtener_catalogo(nombre_catalogo, usar_cache=False)
            
            return {
                'actualizado': True,
                'mensaje': f"Catálogo {nombre_catalogo} actualizado exitosamente",
                'registros': len(catalogo_data['registros']),
                'fecha_actualizacion': catalogo_data['fecha_descarga']
            }
            
        except Exception as e:
            logger.error(f"Error actualizando catálogo {nombre_catalogo}: {e}")
            raise
    
    @staticmethod
    def validar_codigo_en_catalogo(nombre_catalogo: str, codigo: str) -> bool:
        """
        Valida si un código existe en un catálogo específico.
        """
        try:
            catalogo = SATCatalogService.obtener_catalogo(nombre_catalogo)
            
            for registro in catalogo['registros']:
                if registro['codigo'] == codigo:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validando código {codigo} en catálogo {nombre_catalogo}: {e}")
            return False
    
    @staticmethod
    def obtener_descripcion_codigo(nombre_catalogo: str, codigo: str) -> str:
        """
        Obtiene la descripción de un código en un catálogo específico.
        """
        try:
            catalogo = SATCatalogService.obtener_catalogo(nombre_catalogo)
            
            for registro in catalogo['registros']:
                if registro['codigo'] == codigo:
                    return registro['descripcion']
            
            return ""
            
        except Exception as e:
            logger.error(f"Error obteniendo descripción del código {codigo} en catálogo {nombre_catalogo}: {e}")
            return ""
    
    @staticmethod
    def listar_catalogos_disponibles() -> list:
        """
        Lista todos los catálogos disponibles.
        """
        return list(SATCatalogService.CATALOG_FILES.keys())
    
    @staticmethod
    def obtener_estadisticas_catalogos() -> dict:
        """
        Obtiene estadísticas de los catálogos.
        """
        estadisticas = {
            'total_catalogos': len(SATCatalogService.CATALOG_FILES),
            'catalogos_en_cache': 0,
            'catalogos_actualizados': 0,
            'catalogos_desactualizados': 0,
            'detalle': {}
        }
        
        for nombre_catalogo in SATCatalogService.CATALOG_FILES.keys():
            cache_key = f"sat_catalog_{nombre_catalogo}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                estadisticas['catalogos_en_cache'] += 1
                estadisticas['catalogos_actualizados'] += 1
                
                fecha_descarga = datetime.fromisoformat(cached_data['fecha_descarga'].replace('Z', '+00:00'))
                dias_desde_actualizacion = (timezone.now() - fecha_descarga).days
                
                estadisticas['detalle'][nombre_catalogo] = {
                    'en_cache': True,
                    'registros': len(cached_data['registros']),
                    'dias_desde_actualizacion': dias_desde_actualizacion,
                    'actualizado': dias_desde_actualizacion < 7
                }
            else:
                estadisticas['catalogos_desactualizados'] += 1
                estadisticas['detalle'][nombre_catalogo] = {
                    'en_cache': False,
                    'registros': 0,
                    'dias_desde_actualizacion': None,
                    'actualizado': False
                }
        
        return estadisticas
    
    @staticmethod
    def limpiar_cache_catalogos() -> dict:
        """
        Limpia el cache de todos los catálogos.
        """
        catalogos_limpiados = 0
        
        for nombre_catalogo in SATCatalogService.CATALOG_FILES.keys():
            cache_key = f"sat_catalog_{nombre_catalogo}"
            if cache.get(cache_key):
                cache.delete(cache_key)
                catalogos_limpiados += 1
        
        return {
            'catalogos_limpiados': catalogos_limpiados,
            'mensaje': f"Cache limpiado: {catalogos_limpiados} catálogos eliminados"
        }
    
    @classmethod
    def obtener_usos_cfdi(cls, usar_cache: bool = True) -> dict:
        """
        Obtiene el catálogo de usos CFDI con formato para templates.
        
        Returns:
            dict: Lista de usos CFDI con código y descripción
        """
        try:
            # Intentar obtener desde el SAT primero
            catalogo = cls.obtener_catalogo('usos-cfdi', usar_cache)
            
            if catalogo['exito']:
                usos_cfdi = []
                for item in catalogo['items']:
                    usos_cfdi.append({
                        'codigo': item['codigo'],
                        'descripcion': item['descripcion'],
                        'texto_completo': f"{item['codigo']} - {item['descripcion']}"
                    })
                
                return {
                    'exito': True,
                    'usos_cfdi': usos_cfdi,
                    'total': len(usos_cfdi)
                }
            else:
                # Si falla la descarga del SAT, usar catálogo hardcodeado
                logger.warning("No se pudo obtener catálogo del SAT, usando catálogo local")
                return cls._obtener_usos_cfdi_local()
            
        except Exception as e:
            logger.error(f"Error obteniendo usos CFDI: {e}")
            # Fallback a catálogo local
            return cls._obtener_usos_cfdi_local()
    
    @classmethod
    def _obtener_usos_cfdi_local(cls) -> dict:
        """
        Obtiene el catálogo de usos CFDI desde datos locales (hardcoded).
        """
        usos_cfdi = [
            # Usos para personas físicas y morales
            {'codigo': 'G01', 'descripcion': 'Adquisición de mercancías'},
            {'codigo': 'G02', 'descripcion': 'Devoluciones, descuentos o bonificaciones'},
            {'codigo': 'G03', 'descripcion': 'Gastos en general'},
            
            # Usos para inversiones
            {'codigo': 'I01', 'descripcion': 'Construcciones'},
            {'codigo': 'I02', 'descripcion': 'Mobilario y equipo de oficina por inversiones'},
            {'codigo': 'I03', 'descripcion': 'Equipo de transporte'},
            {'codigo': 'I04', 'descripcion': 'Equipo de computo y accesorios'},
            {'codigo': 'I05', 'descripcion': 'Dados, troqueles, moldes, matrices y herramental'},
            {'codigo': 'I06', 'descripcion': 'Comunicaciones telefónicas'},
            {'codigo': 'I07', 'descripcion': 'Comunicaciones satelitales'},
            {'codigo': 'I08', 'descripcion': 'Otra maquinaria y equipo'},
            
            # Usos para deducciones personales
            {'codigo': 'D01', 'descripcion': 'Honorarios médicos, dentales y gastos hospitalarios'},
            {'codigo': 'D02', 'descripcion': 'Gastos médicos por incapacidad o discapacidad'},
            {'codigo': 'D03', 'descripcion': 'Gastos funerales'},
            {'codigo': 'D04', 'descripcion': 'Donativos'},
            {'codigo': 'D05', 'descripcion': 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'},
            {'codigo': 'D06', 'descripcion': 'Aportaciones voluntarias al SAR'},
            {'codigo': 'D07', 'descripcion': 'Primas por seguros de gastos médicos'},
            {'codigo': 'D08', 'descripcion': 'Gastos de transportación escolar obligatoria'},
            {'codigo': 'D09', 'descripcion': 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'},
            {'codigo': 'D10', 'descripcion': 'Pagos por servicios educativos (colegiaturas)'},
            
            # Usos para actividades empresariales
            {'codigo': 'CP01', 'descripcion': 'Pagos'},
            {'codigo': 'CN01', 'descripcion': 'Nómina'},
            
            # Usos para comercio exterior
            {'codigo': 'S01', 'descripcion': 'Sin efectos fiscales'},
            
            # Usos para pagos
            {'codigo': 'P01', 'descripcion': 'Por definir'},
            
            # Usos adicionales para CFDI 4.0
            {'codigo': 'DI01', 'descripcion': 'Honorarios médicos, dentales y gastos hospitalarios'},
            {'codigo': 'DI02', 'descripcion': 'Gastos médicos por incapacidad o discapacidad'},
            {'codigo': 'DI03', 'descripcion': 'Gastos funerales'},
            {'codigo': 'DI04', 'descripcion': 'Donativos'},
            {'codigo': 'DI05', 'descripcion': 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'},
            {'codigo': 'DI06', 'descripcion': 'Aportaciones voluntarias al SAR'},
            {'codigo': 'DI07', 'descripcion': 'Primas por seguros de gastos médicos'},
            {'codigo': 'DI08', 'descripcion': 'Gastos de transportación escolar obligatoria'},
            {'codigo': 'DI09', 'descripcion': 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'},
            {'codigo': 'DI10', 'descripcion': 'Pagos por servicios educativos (colegiaturas)'},
            
            # Usos para actividades empresariales (CFDI 4.0)
            {'codigo': 'DCP01', 'descripcion': 'Pagos'},
            {'codigo': 'DCN01', 'descripcion': 'Nómina'},
            
            # Usos para comercio exterior (CFDI 4.0)
            {'codigo': 'DS01', 'descripcion': 'Sin efectos fiscales'},
            
            # Usos para pagos (CFDI 4.0)
            {'codigo': 'DP01', 'descripcion': 'Por definir'},
        ]
        
        # Agregar texto completo
        for uso in usos_cfdi:
            uso['texto_completo'] = f"{uso['codigo']} - {uso['descripcion']}"
        
        return {
            'exito': True,
            'usos_cfdi': usos_cfdi,
            'total': len(usos_cfdi)
        }