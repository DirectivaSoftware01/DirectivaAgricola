#!/usr/bin/env python3
"""
Script para iniciar Django con el entorno virtual activado automáticamente
Uso: python3 run_django.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Obtener el directorio del script
    script_dir = Path(__file__).parent.absolute()
    
    print("🚀 Iniciando servidor Django de Directiva Agrícola...")
    print(f"📁 Directorio del proyecto: {script_dir}")
    
    # Cambiar al directorio del proyecto
    os.chdir(script_dir)
    
    # Verificar si existe el entorno virtual
    venv_path = script_dir / "venv"
    if not venv_path.exists():
        print("❌ Error: No se encontró el entorno virtual en ./venv")
        print("💡 Ejecuta: python3 -m venv venv")
        sys.exit(1)
    
    # Activar el entorno virtual y ejecutar Django
    if sys.platform == "win32":
        # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        # macOS/Linux
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"
    
    print("📦 Activando entorno virtual...")
    print(f"🐍 Usando Python: {python_exe}")
    
    # Verificar que qrcode esté instalado
    try:
        result = subprocess.run([str(python_exe), "-c", "import qrcode; print('qrcode disponible')"], 
                              capture_output=True, text=True, check=True)
        print("✅ Dependencia qrcode verificada")
    except subprocess.CalledProcessError:
        print("⚠️  Instalando dependencias...")
        subprocess.run([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencias instaladas")
    
    # Iniciar el servidor Django
    print("🌐 Iniciando servidor Django en http://localhost:8000")
    print("💡 Presiona Ctrl+C para detener el servidor")
    print("")
    
    try:
        subprocess.run([str(python_exe), "manage.py", "runserver"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
