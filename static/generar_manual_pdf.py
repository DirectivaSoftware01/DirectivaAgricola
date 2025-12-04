#!/usr/bin/env python3
"""
Script para generar el manual de usuario en formato PDF
Usa WeasyPrint para convertir Markdown a HTML y luego a PDF
"""

import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'directiva_agricola.settings')
import django
django.setup()

from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.conf import settings

def generar_manual_pdf():
    """Genera el PDF del manual de usuario desde el archivo Markdown"""
    
    # Leer el archivo Markdown
    markdown_path = BASE_DIR / 'static' / 'manual_usuario.md'
    
    if not markdown_path.exists():
        print(f"Error: No se encontró el archivo {markdown_path}")
        return False
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convertir Markdown a HTML básico
    # Nota: Esta es una conversión simple. Para una conversión completa de Markdown,
    # se recomienda usar markdown2 o markdown con extensiones
    html_content = markdown_a_html(markdown_content)
    
    # Agregar estilos CSS
    html_completo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Manual de Usuario - Sistema Directiva Agrícola</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Arial', 'Helvetica', sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
            }}
            h1 {{
                color: #2c3e50;
                font-size: 24pt;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                page-break-after: avoid;
            }}
            h2 {{
                color: #34495e;
                font-size: 18pt;
                margin-top: 25px;
                page-break-after: avoid;
            }}
            h3 {{
                color: #555;
                font-size: 14pt;
                margin-top: 20px;
                page-break-after: avoid;
            }}
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            li {{
                margin: 5px 0;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }}
            .imagen-placeholder {{
                border: 2px dashed #ccc;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                background-color: #f9f9f9;
                color: #666;
                font-style: italic;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #3498db;
                color: white;
            }}
            .page-break {{
                page-break-before: always;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generar PDF
    try:
        output_path = BASE_DIR / 'static' / 'manual_usuario.pdf'
        HTML(string=html_completo, base_url=str(BASE_DIR)).write_pdf(
            str(output_path),
            stylesheets=[CSS(string="""
                @page {
                    size: A4;
                    margin: 2cm;
                }
            """)]
        )
        
        print(f"✓ Manual PDF generado exitosamente: {output_path}")
        print(f"  Tamaño del archivo: {output_path.stat().st_size / 1024:.2f} KB")
        return True
        
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return False

def markdown_a_html(markdown_text):
    """Convierte Markdown básico a HTML"""
    import re
    
    lines = markdown_text.split('\n')
    result_lines = []
    in_list = False
    in_ordered_list = False
    in_code_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Saltar líneas vacías (se manejarán después)
        if not stripped:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_ordered_list:
                result_lines.append('</ol>')
                in_ordered_list = False
            result_lines.append('')
            continue
        
        # Encabezados
        if stripped.startswith('#'):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_ordered_list:
                result_lines.append('</ol>')
                in_ordered_list = False
            
            if stripped.startswith('### '):
                result_lines.append(f'<h3>{stripped[4:]}</h3>')
            elif stripped.startswith('## '):
                result_lines.append(f'<h2>{stripped[3:]}</h2>')
            elif stripped.startswith('# '):
                result_lines.append(f'<h1>{stripped[2:]}</h2>')
            continue
        
        # Listas no ordenadas
        if stripped.startswith('- '):
            if in_ordered_list:
                result_lines.append('</ol>')
                in_ordered_list = False
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            content = stripped[2:].strip()
            # Procesar negritas y código dentro de la lista
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
            result_lines.append(f'<li>{content}</li>')
            continue
        
        # Listas ordenadas
        if re.match(r'^\d+\.\s', stripped):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if not in_ordered_list:
                result_lines.append('<ol>')
                in_ordered_list = True
            content = re.sub(r'^\d+\.\s', '', stripped)
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
            result_lines.append(f'<li>{content}</li>')
            continue
        
        # Cerrar listas si hay cambio de contexto
        if in_list or in_ordered_list:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_ordered_list:
                result_lines.append('</ol>')
                in_ordered_list = False
        
        # Marcadores de imagen
        if '[IMAGEN:' in stripped:
            result_lines.append(f'<div class="imagen-placeholder">{stripped}</div>')
            continue
        
        # Párrafos normales
        if stripped and not stripped.startswith('<'):
            # Procesar negritas
            processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            # Procesar código
            processed = re.sub(r'`(.+?)`', r'<code>\1</code>', processed)
            result_lines.append(f'<p>{processed}</p>')
        else:
            result_lines.append(line)
    
    # Cerrar listas abiertas
    if in_list:
        result_lines.append('</ul>')
    if in_ordered_list:
        result_lines.append('</ol>')
    
    return '\n'.join(result_lines)

if __name__ == '__main__':
    print("Generando manual de usuario en PDF...")
    if generar_manual_pdf():
        print("\n✓ Proceso completado exitosamente")
    else:
        print("\n✗ Error en el proceso")
        sys.exit(1)

