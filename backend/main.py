from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import hashlib
import hmac
import json
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = FastAPI(title="PatitasWeb Webhook Server")

# SECRETO DE LEMON SQUEEZY (Configurado en el dashboard de LemonSqueezy)
LEMON_SQUEEZY_WEBHOOK_SECRET = os.getenv("LEMON_SQUEEZY_SECRET", "super_secret_webhook_key_123")

def generar_llave(tipo="mensual"):
    alfabeto = string.ascii_uppercase + string.digits
    parte1 = ''.join(secrets.choice(alfabeto) for _ in range(4))
    parte2 = ''.join(secrets.choice(alfabeto) for _ in range(4))
    
    if tipo == "mensual": sufijo = "M"
    elif tipo == "anual": sufijo = "Y"
    elif tipo == "vitalicia": sufijo = "L"
    else: sufijo = "M"

    llave = f"PATA-{parte1}-{parte2}-{sufijo}"
    return llave

def enviar_llave_correo(email_destino: str, llave: str, tipo_plan: str):
    # Dummy SMTP config, en produccion usar SendGrid o SMTP real
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SENDER_EMAIL = os.getenv("SMTP_USER", "tu_correo@gmail.com")
    SENDER_PASSWORD = os.getenv("SMTP_PASSWORD", "tu_password_app")

    msg = MIMEMultipart()
    msg['From'] = "Soporte Patitas Professional <contacto@patitaspro.com>"
    msg['To'] = email_destino
    msg['Subject'] = f"¡Tu Licencia Oficial Patitas Pro ({tipo_plan.capitalize()})!"

    body = f"""
    ¡Hola!
    
    Gracias por tu compra en Patitas Professional.
    Aquí tienes tu llave oficial de activación:
    
    LLAVE: {llave}
    TIPO DE PLAN: {tipo_plan.capitalize()}
    
    Puedes descargar la última versión del sistema desde aquí:
    [LINK DE DESCARGA DE GOOGLE DRIVE O MEGA]
    
    Instrucciones:
    1. Descarga y extrae el ZIP.
    2. Ejecuta Patitas_Pro.exe.
    3. Ingresa tu llave oficial para desbloquear el sistema.
    
    ¡Bienvenido a la gestión veterinaria del futuro!
    
    Atentamente,
    Daniel Hub System
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        # LOGICA REAL DESACTIVADA POR DEFECTO PARA NO ROMPER SI NO HAY CREDENCIALES
        # server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        # server.starttls()
        # server.login(SENDER_EMAIL, SENDER_PASSWORD)
        # server.send_message(msg)
        # server.quit()
        print(f"[*] [SIMULADOR] Correo enviado a {email_destino} con la llave {llave}")
    except Exception as e:
        print(f"[!] Error al enviar correo: {str(e)}")

@app.post("/webhook/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.body()
        signature = request.headers.get("x-signature")
        
        # Verificar la firma de seguridad (Muy importante en SaaS)
        digest = hmac.new(
            LEMON_SQUEEZY_WEBHOOK_SECRET.encode(), 
            payload, 
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(digest, signature):
            raise HTTPException(status_code=401, detail="Firma Invalida")

        data = json.loads(payload)
        event_name = data.get("meta", {}).get("event_name")
        
        if event_name == "order_created":
            custom_data = data.get("data", {}).get("attributes", {})
            customer_email = custom_data.get("user_email")
            
            # Aqui mapeariamos el product_id con el tipo de plan
            # (Mensual, Anual, Vitalicia). Para el ejemplo usaremos un dummy
            tipo_plan = "anual" # Extraer de data.data.attributes.first_order_item.product_id
            
            # 1. Generar la llave secreta
            nueva_llave = generar_llave(tipo=tipo_plan)
            print(f"[+] Orden detectada para {customer_email}. Llave generada: {nueva_llave}")
            
            # 2. Despachar el correo en segundo plano
            background_tasks.add_task(enviar_llave_correo, customer_email, nueva_llave, tipo_plan)
            
        return {"status": "success"}

    except Exception as e:
        print(f"[!] Webhook Error: {str(e)}")
        raise HTTPException(status_code=400, detail="Error procesando webhook")

@app.get("/")
def home():
    return {"status": "Patitas SaaS Webhook API Online"}
