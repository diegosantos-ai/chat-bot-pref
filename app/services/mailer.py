import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.settings import settings

logger = logging.getLogger(__name__)


class Mailer:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASS
        self.managers = [
            e.strip() for e in settings.MANAGER_EMAILS.split(",") if e.strip()
        ]

    def send_escalation_email(
        self,
        user_query: str,
        user_contact: str = "Desconhecido",
        platform: str = "N/A",
        user_name: str | None = None,
    ) -> bool:
        """
        Envia email de escalonamento para os gerentes configurados.
        Retorna True se enviou com sucesso.

        Args:
            user_query: Pergunta/mensagem do usuário
            user_contact: Identificador de contato (ex: @username, ID, etc)
            platform: Plataforma de origem (Instagram, Facebook, Web)
            user_name: Nome completo do usuário (opcional)
        """
        if not self.host or not self.user or not self.managers:
            logger.warning(
                "SMTP ou Emails de Gerentes não configurados. Escalation falhou."
            )
            return False

        # Formata o contato para exibição
        contact_display = user_contact
        if user_name and user_name != user_contact:
            contact_display = f"{user_name} ({user_contact})"

        subject = f"[TerezIA] Ticket Escalado - {contact_display}"

        body = f"""
        <h2>Solicitação Escalada</h2>
        <p>A TerezIA não conseguiu responder satisfatoriamente à seguinte questão:</p>
        <blockquote style="border-left: 3px solid #ccc; padding-left: 10px; margin: 10px 0; color: #555;">
            "{user_query}"
        </blockquote>
        
        <h3>Informações do Usuário</h3>
        <ul>
            <li><strong>Contato:</strong> {contact_display}</li>
            <li><strong>Plataforma:</strong> {platform}</li>
            <li><strong>ID Interno:</strong> {user_contact}</li>
        </ul>
        
        <hr>
        <p><i>Este é um email automático. Por favor, entre em contato com o cidadão.</i></p>
        <p><i>Para responder via Instagram/Facebook, procure pelo usuário: {user_contact}</i></p>
        """

        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["To"] = ", ".join(self.managers)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, self.managers, msg.as_string())
            server.quit()
            logger.info(
                f"Email de escalonamento enviado para {len(self.managers)} gerentes."
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email de escalonamento: {e}")
            return False


mailer = Mailer()
