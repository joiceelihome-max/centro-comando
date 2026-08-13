"""
modules/administrativo.py — Módulo Administrativo
Resumo executivo de e-mails, gestão de prazos e compromissos
"""
import os, json, logging
from datetime import datetime, timedelta
from flask import Blueprint, request
import anthropic
from config import get_table, requer_auth, resposta, erro

logger = logging.getLogger(__name__)
bp     = Blueprint("administrativo", __name__, url_prefix="/administrativo")
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

PROMPT_EMAIL = """Analise o e-mail e retorne SOMENTE este JSON:
{
  "resumo": "máximo 2 frases objetivas",
  "prazo": "YYYY-MM-DD ou null",
  "horario_prazo": "HH:MM ou null",
  "valor_envolvido": 0.00,
  "urgencia": "Crítica|Alta|Média|Baixa",
  "tipo": "Fatura|Contrato|Prazo_Legal|Reunião|Lembrete|Outros",
  "criar_compromisso": true
}
Crítica=prazo<48h ou multa; Alta=<7 dias ou >R$1000; Média=7-30 dias; Baixa=informativo."""


def analisar_email(assunto: str, corpo: str, remetente: str) -> dict:
    try:
        conteudo = f"De: {remetente}\nAssunto: {assunto}\n\n{corpo[:4000]}"
        resp = client.messages.create(
            model="claude-opus-4-5", max_tokens=600,
            messages=[{"role": "user", "content": f"{PROMPT_EMAIL}\n\nE-MAIL:\n{conteudo}"}],
        )
        texto = resp.content[0].text.strip().lstrip("```json").lstrip("```").rstrip("```")
        return json.loads(texto)
    except Exception as e:
        logger.error(f"Erro IA e-mail: {e}")
        return {"erro": True, "detalhes": str(e)}


@bp.route("/processar-email", methods=["POST"])
@requer_auth
def processar_email():
    body    = request.get_json(silent=True) or {}
    assunto = body.get("assunto", "Sem assunto")
    remetente = body.get("remetente", "")
    corpo   = body.get("corpo", "")
    data_rec = body.get("data_recebimento", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if not corpo: return erro("'corpo' obrigatório", 400)

    analise = analisar_email(assunto, corpo, remetente)
    if analise.get("erro"): return erro(f"Falha IA: {analise.get('detalhes')}", 422)

    # Salva e-mail
    tab_email = get_table("Emails_Notificacoes")
    reg = tab_email.create({k: v for k, v in {
        "Assunto_Original":       assunto[:255],
        "Remetente":              remetente,
        "Data_Recebimento":       data_rec,
        "Conteudo_Original":      corpo[:10000],
        "Resumo_Executivo":       analise.get("resumo", ""),
        "Prazo_Identificado":     analise.get("prazo"),
        "Valor_Envolvido":        float(analise.get("valor_envolvido") or 0),
        "Urgencia":               analise.get("urgencia", "Baixa"),
        "Tipo":                   analise.get("tipo", "Outros"),
        "Status_Acao":            "Novo",
        "Sincronizado_Calendario": False,
    }.items() if v is not None})

    # Cria compromisso se IA indicou
    comp_id = None
    if analise.get("criar_compromisso") and analise.get("prazo"):
        data_hora = analise["prazo"]
        if analise.get("horario_prazo"): data_hora += f" {analise['horario_prazo']}"
        else: data_hora += " 09:00"
        try:
            comp = get_table("Compromissos").create({
                "Titulo":          f"[{analise.get('tipo','Email')}] {assunto[:80]}",
                "Data_Hora_Inicio": data_hora,
                "Tipo":            analise.get("tipo", "Prazo"),
                "Urgencia":        analise.get("urgencia", "Média"),
                "Status":          "Pendente",
                "Lembrete_Enviado": False,
            })
            comp_id = comp["id"]
            tab_email.update(reg["id"], {"Sincronizado_Calendario": True})
        except Exception as e: logger.warning(f"Compromisso não criado: {e}")

    return resposta(data={
        "email_id": reg["id"], "urgencia": analise.get("urgencia"),
        "resumo": analise.get("resumo"), "prazo": analise.get("prazo"),
        "valor": analise.get("valor_envolvido"),
        "compromisso_criado": comp_id is not None, "compromisso_id": comp_id,
        "requer_alerta_imediato": analise.get("urgencia") in ["Crítica", "Alta"],
    })


@bp.route("/compromissos-hoje", methods=["GET"])
@requer_auth
def compromissos_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    regs = get_table("Compromissos").all(
        formula=f"AND(FIND('{hoje}',{{Data_Hora_Inicio}})>0,{{Status}}!='Cancelado')",
        sort=["Data_Hora_Inicio"]
    )
    return resposta(data={"data": hoje, "total": len(regs), "compromissos": [
        {"titulo": r["fields"].get("Titulo"),
         "hora":   (r["fields"].get("Data_Hora_Inicio") or "")[-5:],
         "tipo":   r["fields"].get("Tipo"),
         "urgencia": r["fields"].get("Urgencia")}
        for r in regs
    ]})


@bp.route("/prazos-proximos", methods=["GET"])
@requer_auth
def prazos_proximos():
    dias   = int(request.args.get("dias", 7))
    hoje   = datetime.now().strftime("%Y-%m-%d")
    limite = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    regs   = get_table("Emails_Notificacoes").all(
        formula=f"AND({{Prazo_Identificado}}>='{hoje}',{{Prazo_Identificado}}<='{limite}',{{Status_Acao}}!='Resolvido')",
        sort=["Prazo_Identificado"]
    )
    return resposta(data={"dias": dias, "total": len(regs), "prazos": [
        {"assunto": r["fields"].get("Assunto_Original"),
         "prazo":   r["fields"].get("Prazo_Identificado"),
         "urgencia":r["fields"].get("Urgencia"),
         "valor":   r["fields"].get("Valor_Envolvido"),
         "resumo":  r["fields"].get("Resumo_Executivo")}
        for r in regs
    ]})
