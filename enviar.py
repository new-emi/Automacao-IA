import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import gspread

# ── Configurações (valores reais injetados via Secrets em produção) ──
SHEET_ID         = "<ID_DA_PLANILHA>"
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
GMAIL_USER       = os.environ.get("GMAIL_USER", "remetente@dominio.com")
GMAIL_APP_PASS   = os.environ.get("GMAIL_APP_PASS", "xxxx xxxx xxxx xxxx")

# ── 1. Conectar na planilha ─────────────────────────────────────────
gc = gspread.service_account(filename=CREDENTIALS_FILE)
sh = gc.open_by_key(SHEET_ID)

# "Hoje" no fuso da Flórida (Eastern Time), imune a horário de verão
today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()

# ── 2. Mensagem do dia (Página2) ────────────────────────────────────
messages = sh.worksheet("Página2").get_all_records()
row = next((r for r in messages if str(r.get("DAY", "")).strip() == today), None)

if not row:
    print(f"[{today}] Nenhuma mensagem para hoje. Nada será enviado.")
    raise SystemExit

# ── 3. Destinatários (Página1) ──────────────────────────────────────
recipients = sh.worksheet("Página1").get_all_records()

# ── 4. Enviar ───────────────────────────────────────────────────────
server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(GMAIL_USER, GMAIL_APP_PASS)

sent = 0
for r in recipients:
    email = str(r.get("EMAIL", "")).strip()
    nome  = str(r.get("FIRST NAME") or r.get("NOME") or "").strip()
    if not email:
        continue

    html_body = (
        f"<p>Hello {nome} - {row['MESSAGES']}</p>\n"
        f"<img src=\"{row['IMAGE_URL']}\" alt=\"Imagem do dia\" />"
    )

    msg = MIMEMultipart()
    msg["From"] = f"Nome do Remetente <{GMAIL_USER}>"
    msg["To"] = email
    msg["Subject"] = f"How are you going {nome}?"
    msg.attach(MIMEText(html_body, "html"))

    server.sendmail(GMAIL_USER, [email], msg.as_string())
    sent += 1
    print(f"Enviado para {email}")
    time.sleep(1)   # pausa anti-sobrecarga entre envios

server.quit()
print(f"Concluído: {sent} e-mail(s) enviado(s).")
