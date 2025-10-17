#!/bin/bash

echo "🔍 Monitoreando propagación DNS para agricola.directiva.mx"
echo "📍 IP esperada: 54.212.80.37"
echo ""

while true; do
    CURRENT_IP=$(nslookup agricola.directiva.mx | grep "Address:" | tail -1 | awk '{print $2}')
    echo "$(date): IP actual = $CURRENT_IP"
    
    if [ "$CURRENT_IP" = "54.212.80.37" ]; then
        echo "✅ ¡DNS propagado correctamente!"
        break
    else
        echo "⏳ Esperando propagación DNS... (30 segundos)"
        sleep 30
    fi
done

echo ""
echo "🚀 Ahora podemos configurar SSL"
