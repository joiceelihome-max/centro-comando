"""
modules/familiar.py — Módulo Familiar
Lembretes lúdicos, sistema XP, agenda escolar
"""
import os, logging
from datetime import datetime, timedelta
from flask import Blueprint, request
import anthropic
from config import get_table, requer_auth, resposta, erro

logger = logging.getLogger(__name__)
bp     = Blueprint("familiar", __name__, url_prefix="/familiar")
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

NIVEIS = [(0,"⭐ Iniciante"),(500,"🌟 Explorador"),(1500,"🦸 Herói"),(3000,"🏆 Campeão"),(6000,"👑 Lenda")]

def calcular_nivel(xp: int) -> str:
    nivel = NIVEIS[0][1]
    for minimo, nome in NIVEIS:
        if xp >= minimo: nivel = nome
    return nivel


def msg_crianca(nome: str, idade: int, xp: int, nivel: str, tarefas: list) -> str:
    lista = "\n".join(f"- {t.get('Emoji_Icone','')} {t.get('Titulo_Tarefa')} (+{t.get('Pontos_Recompensa',0)} XP)" for t in tarefas)
    prompt = f"""Crie mensagem WhatsApp para {nome} ({idade} anos).
Tarefas hoje:\n{lista}\nXP: {xp} — Nível: {nivel}
Regras: máx 4 linhas, emojis, mencione pontos, tom de game, motivador.
Retorne APENAS o texto, sem JSON."""
    try:
        resp = client.messages.create(model="claude-opus-4-5", max_tokens=250,
                                       messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text.strip()
    except Exception:
        return f"🌟 Bom dia, {nome}! Você tem {len(tarefas)} missões hoje!\n⚡ Complete e ganhe XP!\n🏆 Nível atual: {nivel}\n💪 Bora, campeão!"


@bp.route("/briefing-diario", methods=["POST"])
@requer_auth
def briefing_diario():
    hoje    = datetime.now().strftime("%Y-%m-%d")
    membros = get_table("Membros_Familia").all()
    tarefas_hoje = get_table("Tarefas_Familiares").all(
        formula=f"AND({{Data_Prazo}}='{hoje}',{{Status}}!='Concluída')"
    )
    mensagens = []
    for m in membros:
        f    = m["fields"]
        nome = f.get("Nome", "")
        xp   = int(f.get("Pontos_XP", 0))
        nivel = calcular_nivel(xp)
        tarefas_membro = [t["fields"] for t in tarefas_hoje
                          if nome in str(t["fields"].get("Responsavel", []))]
        if f.get("Tipo") in ["Criança", "Adolescente"] and tarefas_membro:
            msg = msg_crianca(nome, int(f.get("Idade", 8)), xp, nivel, tarefas_membro)
        else:
            amanha  = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            faturas = get_table("Faturas_Recibos").all(
                formula=f"AND({{Data_Vencimento}}<='{amanha}',{{Status_Pagamento}}='Pendente')"
            )
            emails_urg = get_table("Emails_Notificacoes").all(
                formula="AND({Urgencia}!='Baixa',{Status_Acao}='Novo')"
            )
            linhas = ["🗓️ *Seu Briefing de Hoje*\n"]
            if tarefas_membro:
                linhas.append("✅ *SUAS TAREFAS*")
                for t in tarefas_membro: linhas.append(f"  {t.get('Emoji_Icone','')} {t.get('Titulo_Tarefa')}")
                linhas.append("")
            if faturas:
                linhas.append("⚠️ *FATURAS VENCENDO*")
                for fat in faturas[:3]:
                    linhas.append(f"  💰 {fat['fields'].get('Item_Descricao')} — R$ {fat['fields'].get('Valor',0):.2f}")
                linhas.append("")
            if emails_urg:
                linhas.append("📧 *E-MAILS URGENTES*")
                for e in emails_urg[:2]: linhas.append(f"  🔴 {str(e['fields'].get('Assunto_Original',''))[:50]}")
            msg = "\n".join(linhas) if len(linhas) > 1 else "✅ Nada urgente hoje. Bom dia! 😊"

        mensagens.append({"nome": nome, "whatsapp": f.get("Email_Whatsapp",""),
                          "tipo": f.get("Tipo"), "mensagem": msg, "tarefas": len(tarefas_membro)})

    return resposta(data={"data": hoje, "total": len(mensagens), "mensagens": mensagens})


@bp.route("/completar-tarefa", methods=["POST"])
@requer_auth
def completar_tarefa():
    body = request.get_json(silent=True) or {}
    tarefa_id = body.get("tarefa_id")
    membro_nome = body.get("membro_nome")
    if not tarefa_id: return erro("'tarefa_id' obrigatório", 400)

    try:
        tab_t = get_table("Tarefas_Familiares")
        tarefa = tab_t.get(tarefa_id)
        pontos = int(tarefa["fields"].get("Pontos_Recompensa", 0))
        tab_t.update(tarefa_id, {"Status": "Concluída"})

        celebracao = f"✅ +{pontos} XP!"
        if membro_nome:
            membros = get_table("Membros_Familia").all(formula=f"{{Nome}}='{membro_nome}'")
            if membros:
                m        = membros[0]
                xp_ant   = int(m["fields"].get("Pontos_XP", 0))
                xp_novo  = xp_ant + pontos
                nv_ant   = calcular_nivel(xp_ant)
                nv_novo  = calcular_nivel(xp_novo)
                get_table("Membros_Familia").update(m["id"], {"Pontos_XP": xp_novo, "Nivel": nv_novo})
                celebracao = (f"🎉 SUBIU DE NÍVEL! {nv_ant} → {nv_novo}! 🚀"
                              if nv_novo != nv_ant else f"✅ +{pontos} XP! Total: {xp_novo} pts!")
        return resposta(data={"pontos": pontos, "celebracao": celebracao})
    except Exception as e:
        return erro(str(e))


@bp.route("/ranking", methods=["GET"])
@requer_auth
def ranking():
    membros = get_table("Membros_Familia").all(sort=["-Pontos_XP"])
    return resposta(data={"ranking": [
        {"posicao": i+1, "nome": r["fields"].get("Nome"),
         "xp": r["fields"].get("Pontos_XP", 0),
         "nivel": calcular_nivel(int(r["fields"].get("Pontos_XP", 0))),
         "avatar": r["fields"].get("Avatar_Emoji", "👤")}
        for i, r in enumerate(membros)
    ]})


@bp.route("/alerta-vencimento", methods=["POST"])
@requer_auth
def alerta_vencimento():
    dias   = int((request.get_json(silent=True) or {}).get("dias", 3))
    hoje   = datetime.now().strftime("%Y-%m-%d")
    limite = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    regs   = get_table("Agenda_Escolar").all(
        formula=f"AND({{Data_Prazo}}>='{hoje}',{{Data_Prazo}}<='{limite}',{{Status}}!='Concluído')"
    )
    return resposta(data={"dias": dias, "total": len(regs), "alertas": [
        {"titulo": r["fields"].get("Titulo"), "disciplina": r["fields"].get("Disciplina"),
         "data_prazo": r["fields"].get("Data_Prazo"), "tipo": r["fields"].get("Tipo"),
         "urgencia": r["fields"].get("Urgencia")}
        for r in regs
    ]})
