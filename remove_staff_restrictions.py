#!/usr/bin/env python3
"""
Script para eliminar todas las restricciones de staff del sistema
"""

import os
import re

def remove_staff_restrictions(file_path):
    """Eliminar restricciones de staff de un archivo"""
    print(f"Procesando archivo: {file_path}")
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Crear backup
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"Backup creado: {backup_path}")
    
    # Procesar líneas
    new_lines = []
    i = 0
    removed_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Buscar patrón de restricción de staff
        if re.search(r'if not request\.user\.is_staff:', line):
            print(f"Encontrada restricción en línea {i+1}: {line.strip()}")
            
            # Eliminar esta línea y las siguientes 2 líneas (generalmente contienen return redirect)
            # Verificar que las siguientes líneas sean parte del bloque
            j = i + 1
            while j < len(lines) and j < i + 3:
                next_line = lines[j].strip()
                if (next_line.startswith('return redirect') or 
                    next_line.startswith('return') or
                    next_line == '' or
                    next_line.startswith('#')):
                    j += 1
                else:
                    break
            
            print(f"Eliminando líneas {i+1} a {j}")
            removed_count += (j - i)
            i = j
        else:
            new_lines.append(line)
            i += 1
    
    # Escribir archivo modificado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Procesado {file_path}: {removed_count} líneas eliminadas")
    return removed_count

def main():
    """Función principal"""
    files_to_process = [
        'core/views/main_views.py',
        'core/views/emisor_ajax_views.py'
    ]
    
    total_removed = 0
    
    for file_path in files_to_process:
        if os.path.exists(file_path):
            removed = remove_staff_restrictions(file_path)
            total_removed += removed
        else:
            print(f"❌ Archivo no encontrado: {file_path}")
    
    print(f"\n🎉 Proceso completado!")
    print(f"Total de líneas eliminadas: {total_removed}")
    print(f"Archivos procesados: {len(files_to_process)}")

if __name__ == "__main__":
    main()
