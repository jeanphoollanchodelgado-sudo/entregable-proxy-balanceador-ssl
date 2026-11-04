# Entregable 2 - Proxy inverso y balanceador

Prototipo local para el proyecto de Sistemas Operativos. El proxy Python distribuye solicitudes HTTP GET mediante round-robin entre dos backends, consulta `/health` y publica `/health` en el proxy. Incluye cabecera `X-Forwarded-For` y respuesta `X-Backend` para observar el enrutamiento.

## Requisitos
Python 3.10 o superior; solo biblioteca estandar.

## Ejecucion (tres terminales)
1. `python src/backend.py 9001`
2. `set BACKEND_NAME=backend-2` (PowerShell: `$env:BACKEND_NAME="backend-2"`), luego `python src/backend.py 9002`
3. `python src/proxy.py`
En Linux/macOS, use `BACKEND_NAME=backend-2 python3 src/backend.py 9002`.

Pruebas: `curl http://127.0.0.1:8080/health` y repita `curl http://127.0.0.1:8080/demo`. Las respuestas deben alternar entre 9001 y 9002. Detenga un backend para observar que el health check lo excluye.

## Alcance
El prototipo es HTTP local, sin TLS ni interfaz grafica. Las estructuras de sockets, concurrencia y llamadas del kernel son gestionadas por la biblioteca estandar y el sistema operativo; el ajuste de `sysctl.conf` es una propuesta para una VM Linux, no se aplica automaticamente. No se declara probado epoll directamente ni cero-copy. Para despliegue productivo, usar NGINX/HAProxy, certificados TLS y limites de recursos revisados.

## HTTPS de prueba con TLS 1.3 en Windows
Con el certificado autofirmado creado en `cert/server.crt` y `cert/server.key`, configure en PowerShell: `$env:TLS_PORT="8443"`; `$env:TLS_CERT="cert/server.crt"`; `$env:TLS_KEY="cert/server.key"`; luego inicie `py src\proxy.py`. La instancia sirve HTTP en 8080 y HTTPS en 8443. Pruebe con `curl.exe -k -i https://localhost:8443/health` y `curl.exe -k -i https://localhost:8443/demo`. `-k` permite a curl aceptar el certificado autofirmado durante esta prueba. El contexto TLS queda restringido a TLS 1.3. No incluya la clave privada en el repositorio o en un paquete compartido.
