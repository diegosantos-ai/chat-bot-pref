import smtplib
import sys
from email.mime.text import MIMEText

# Tente carregar do .env se existir, senão usa input
try:
    from app.settings import settings
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_pass = settings.SMTP_PASS
except Exception as e:
    print(f"[WARN] Erro ao importar settings: {e}")
    # Fallback se app não estiver configurado
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = ""
    smtp_pass = ""

def test_smtp_connection():
    print("=== Teste de Conexão SMTP (Gmail) ===")
    
    # Se não tiver configurado no settings, pede input
    host = smtp_user and smtp_host or "smtp.gmail.com"
    port = smtp_user and smtp_port or 587
    user = smtp_user or input("Seu Email Gmail: ")
    password = smtp_pass or input("Sua Senha de App (16 digitos): ")
    
    recipient = input(f"Email de destino (para teste) [{user}]: ") or user

    print(f"\nTentando conectar em {host}:{port} como {user}...")

    try:
        server = smtplib.SMTP(host, port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        print("Conexão TLS estabelecida.")
        
        server.login(user, password)
        print("Login realizado com sucesso!")
        
        msg = MIMEText("Este é um email de teste da {bot_name}.")
        msg['Subject'] = "Teste {bot_name} - SMTP OK"
        msg['From'] = user
        msg['To'] = recipient
        
        server.sendmail(user, recipient, msg.as_string())
        print(f"Email enviado para {recipient} com sucesso!")
        
        server.quit()
        return True

    except smtplib.SMTPAuthenticationError:
        print("\n[ERRO] Falha na autenticação.")
        print("Dica: Se você usa 2FA no Gmail, você PRECISA usar uma 'Senha de App'.")
        print("Vá em: Google Account > Security > 2-Step Verification > App passwords.")
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Se passado argumentos (ex: pelo terminal)
        pass 
    test_smtp_connection()
