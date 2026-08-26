"""
modules/dashboard.py — Endpoint agregado para o painel visual (Centro de Comando)
Leitura pública (somente GET, sem dados sensíveis de auth) para alimentar o dashboard HTML.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from config import get_table

logger = logging.getLogger(__name__)
bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

NIVEIS = [(0, "⭐ Iniciante"), (500, "🌟 Explorador"), (1500, "🦸 Herói"), (3000, "🏆 Campeão"), (6000, "👑 Lenda")]


def _calcular_nivel(xp: int) -> str:
    nivel = NIVEIS[0][1]
    for minimo, nome in NIVEIS:
        if xp >= minimo:
            nivel = nome
    return nivel


@bp.route("/resumo", methods=["GET"])
def resumo():
    hoje = datetime.now()
    hoje_str = hoje.strftime("%Y-%m-%d")
    mes_str = hoje.strftime("%Y-%m")

    # --- Financeiro ---
    faturas = get_table("Faturas_Recibos").all()
    pendentes = [r for r in faturas if r["fields"].get("Status_Pagamento") == "Pendente"]
    pagos = [r for r in faturas if r["fields"].get("Status_Pagamento") == "Pago"]
    total_pendente = round(sum(r["fields"].get("Valor", 0) for r in pendentes), 2)
    total_pago = round(sum(r["fields"].get("Valor", 0) for r in pagos), 2)
    saldo_estimado = round(total_pago - total_pendente, 2)

    proximos_vencimentos = [
        {
            "item": r["fields"].get("Item_Descricao"),
            "valor": r["fields"].get("Valor"),
            "vencimento": r["fields"].get("Data_Vencimento"),
            "categoria": r["fields"].get("Categoria"),
            "status": r["fields"].get("Status_Pagamento"),
        }
        for r in sorted(pendentes, key=lambda x: x["fields"].get("Data_Vencimento") or "9999-99-99")[:6]
    ]

    # --- Administrativo ---
    compromissos_raw = get_table("Compromissos").all(
        formula=f"AND(FIND('{hoje_str}',{{Data_Hora_Inicio}})>0,{{Status}}!='Cancelado')",
        sort=["Data_Hora_Inicio"],
    )
    compromissos_hoje = [
        {
            "titulo": r["fields"].get("Titulo"),
            "hora": (r["fields"].get("Data_Hora_Inicio") or "")[-5:],
            "tipo": r["fields"].get("Tipo"),
            "urgencia": r["fields"].get("Urgencia"),
        }
        for r in compromissos_raw
    ]

    limite = (hoje + timedelta(days=7)).strftime("%Y-%m-%d")
    emails_urg = get_table("Emails_Notificacoes").all(
        formula=f"AND({{Prazo_Identificado}}>='{hoje_str}',{{Prazo_Identificado}}<='{limite}',{{Status_Acao}}!='Resolvido')",
        sort=["Prazo_Identificado"],
    )
    prazos_proximos = [
        {
            "assunto": r["fields"].get("Assunto_Original"),
            "prazo": r["fields"].get("Prazo_Identificado"),
            "urgencia": r["fields"].get("Urgencia"),
            "valor": r["fields"].get("Valor_Envolvido"),
        }
        for r in emails_urg
    ]
    total_emails_criticos = len([e for e in emails_urg if e["fields"].get("Urgencia") == "Crítica"])

    # --- Família ---
    membros = get_table("Membros_Familia").all(sort=["-Pontos_XP"])
    ranking = [
        {
            "posicao": i + 1,
            "nome": r["fields"].get("Nome"),
            "xp": r["fields"].get("Pontos_XP", 0),
            "nivel": _calcular_nivel(int(r["fields"].get("Pontos_XP", 0))),
            "avatar": r["fields"].get("Avatar_Emoji", "👤"),
        }
        for i, r in enumerate(membros)
    ]

    tarefas_raw = get_table("Tarefas_Familiares").all(formula="{Status}!='Concluída'")
    tarefas_semana = [
        {
            "titulo": r["fields"].get("Titulo_Tarefa"),
            "emoji": r["fields"].get("Emoji_Icone"),
            "pontos": r["fields"].get("Pontos_Recompensa"),
            "prazo": r["fields"].get("Data_Prazo"),
            "status": r["fields"].get("Status"),
        }
        for r in tarefas_raw
    ]

    limite_escola = (hoje + timedelta(days=14)).strftime("%Y-%m-%d")
    agenda_raw = get_table("Agenda_Escolar").all(
        formula=f"AND({{Data_Prazo}}>='{hoje_str}',{{Data_Prazo}}<='{limite_escola}',{{Status}}!='Concluído')",
        sort=["Data_Prazo"],
    )
    agenda_escolar = [
        {
            "titulo": r["fields"].get("Titulo"),
            "disciplina": r["fields"].get("Disciplina"),
            "prazo": r["fields"].get("Data_Prazo"),
            "tipo": r["fields"].get("Tipo"),
            "urgencia": r["fields"].get("Urgencia"),
        }
        for r in agenda_raw
    ]

    return jsonify({
        "status": "ok",
        "atualizado_em": hoje.isoformat(timespec="seconds"),
        "financeiro": {
            "mes_referencia": mes_str,
            "saldo_estimado": saldo_estimado,
            "total_pendente": total_pendente,
            "total_pago": total_pago,
            "proximos_vencimentos": proximos_vencimentos,
        },
        "administrativo": {
            "compromissos_hoje": compromissos_hoje,
            "prazos_proximos": prazos_proximos,
            "total_emails_criticos": total_emails_criticos,
        },
        "familia": {
            "ranking": ranking,
            "tarefas_semana": tarefas_semana,
            "agenda_escolar": agenda_escolar,
        },
    })


@bp.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    return response
