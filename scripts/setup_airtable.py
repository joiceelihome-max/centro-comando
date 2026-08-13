"""
scripts/setup_airtable.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cria TODAS as tabelas e campos do projeto no Airtable via API.
Execute UMA ÚNICA VEZ após criar a base:

  python scripts/setup_airtable.py

Requer AIRTABLE_API_KEY e AIRTABLE_BASE_ID no .env
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os, sys, time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
META_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

if not API_KEY or not BASE_ID:
    print("❌ AIRTABLE_API_KEY e AIRTABLE_BASE_ID obrigatórios no .env")
    sys.exit(1)


def criar_tabela(nome: str, campos: list[dict]) -> dict:
    """Cria uma tabela no Airtable com os campos especificados."""
    payload = {"name": nome, "fields": campos}
    resp = requests.post(META_URL, headers=HEADERS, json=payload)
    if resp.status_code == 200:
        print(f"  ✅ Tabela '{nome}' criada")
        return resp.json()
    elif resp.status_code == 422 and "already exists" in resp.text:
        print(f"  ⚠️  Tabela '{nome}' já existe — pulando")
        return {}
    else:
        print(f"  ❌ Erro ao criar '{nome}': {resp.status_code} — {resp.text[:200]}")
        return {}


# ── Definição das tabelas ────────────────────────────────────

TABELAS = [
    {
        "nome": "Faturas_Recibos",
        "campos": [
            {"name": "Item_Descricao",    "type": "multilineText"},
            {"name": "Valor",             "type": "currency", "options": {"precision": 2, "symbol": "R$"}},
            {"name": "Data_Vencimento",   "type": "date",     "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Codigo_Pix_Bruto",  "type": "multilineText"},
            {"name": "QR_Code_URL",       "type": "url"},
            {"name": "Categoria",         "type": "singleSelect", "options": {"choices": [
                {"name": "Moradia"},{"name": "Alimentação"},{"name": "Saúde"},
                {"name": "Educação"},{"name": "Transporte"},{"name": "Lazer"},
                {"name": "Empresarial"},{"name": "Outros"},
            ]}},
            {"name": "Status_Pagamento",  "type": "singleSelect", "options": {"choices": [
                {"name": "Pendente", "color": "yellowLight2"},
                {"name": "Pago",     "color": "greenLight2"},
                {"name": "Atrasado", "color": "redLight2"},
            ]}},
            {"name": "Data_Pagamento",    "type": "date",    "options": {"dateFormat": {"name": "iso"}}},
            {"name": "IA_Status",         "type": "singleSelect", "options": {"choices": [
                {"name": "Pendente"},{"name": "Processando"},
                {"name": "Concluído"},{"name": "Erro"},
            ]}},
            {"name": "Arquivo_Original",  "type": "multipleAttachments"},
        ],
    },
    {
        "nome": "Emails_Notificacoes",
        "campos": [
            {"name": "Assunto_Original",       "type": "singleLineText"},
            {"name": "Remetente",              "type": "email"},
            {"name": "Data_Recebimento",       "type": "dateTime", "options": {
                "dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "America/Sao_Paulo"
            }},
            {"name": "Conteudo_Original",      "type": "multilineText"},
            {"name": "Resumo_Executivo",       "type": "multilineText"},
            {"name": "Prazo_Identificado",     "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Valor_Envolvido",        "type": "currency", "options": {"precision": 2, "symbol": "R$"}},
            {"name": "Urgencia",               "type": "singleSelect", "options": {"choices": [
                {"name": "Crítica", "color": "redBright"},
                {"name": "Alta",    "color": "orange"},
                {"name": "Média",   "color": "yellow"},
                {"name": "Baixa",   "color": "green"},
            ]}},
            {"name": "Tipo",                   "type": "singleSelect", "options": {"choices": [
                {"name": "Fatura"},{"name": "Contrato"},{"name": "Prazo_Legal"},
                {"name": "Reunião"},{"name": "Lembrete"},{"name": "Outros"},
            ]}},
            {"name": "Status_Acao",            "type": "singleSelect", "options": {"choices": [
                {"name": "Novo"},{"name": "Em Análise"},{"name": "Resolvido"},
            ]}},
            {"name": "Sincronizado_Calendario","type": "checkbox"},
        ],
    },
    {
        "nome": "Compromissos",
        "campos": [
            {"name": "Titulo",           "type": "singleLineText"},
            {"name": "Data_Hora_Inicio", "type": "dateTime", "options": {
                "dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "America/Sao_Paulo"
            }},
            {"name": "Data_Hora_Fim",    "type": "dateTime", "options": {
                "dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "America/Sao_Paulo"
            }},
            {"name": "Local",            "type": "singleLineText"},
            {"name": "Tipo",             "type": "singleSelect", "options": {"choices": [
                {"name": "Reunião"},{"name": "Prazo"},{"name": "Consulta"},
                {"name": "Escola"},{"name": "Pessoal"},{"name": "Outros"},
            ]}},
            {"name": "Urgencia",         "type": "singleSelect", "options": {"choices": [
                {"name": "Alta"},{"name": "Média"},{"name": "Baixa"},
            ]}},
            {"name": "Status",           "type": "singleSelect", "options": {"choices": [
                {"name": "Pendente"},{"name": "Confirmado"},{"name": "Cancelado"},
            ]}},
            {"name": "Lembrete_Enviado", "type": "checkbox"},
        ],
    },
    {
        "nome": "Membros_Familia",
        "campos": [
            {"name": "Nome",           "type": "singleLineText"},
            {"name": "Tipo",           "type": "singleSelect", "options": {"choices": [
                {"name": "Adulto"},{"name": "Adolescente"},{"name": "Criança"},
            ]}},
            {"name": "Idade",          "type": "number",   "options": {"precision": 0}},
            {"name": "Pontos_XP",      "type": "number",   "options": {"precision": 0}},
            {"name": "Nivel",          "type": "singleSelect", "options": {"choices": [
                {"name": "⭐ Iniciante"},{"name": "🌟 Explorador"},
                {"name": "🦸 Herói"},{"name": "🏆 Campeão"},{"name": "👑 Lenda"},
            ]}},
            {"name": "Avatar_Emoji",   "type": "singleLineText"},
            {"name": "Email_Whatsapp", "type": "singleLineText"},
        ],
    },
    {
        "nome": "Tarefas_Familiares",
        "campos": [
            {"name": "Titulo_Tarefa",       "type": "singleLineText"},
            {"name": "Emoji_Icone",         "type": "singleLineText"},
            {"name": "Descricao_Ludica",    "type": "multilineText"},
            {"name": "Data_Prazo",          "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Status",              "type": "singleSelect", "options": {"choices": [
                {"name": "A Fazer",      "color": "grayLight2"},
                {"name": "Em Progresso", "color": "blueLight2"},
                {"name": "Concluída",    "color": "greenLight2"},
                {"name": "Bônus",        "color": "yellowLight2"},
            ]}},
            {"name": "Pontos_Recompensa",   "type": "number",   "options": {"precision": 0}},
            {"name": "Recompensa_Descricao","type": "singleLineText"},
            {"name": "Categoria",           "type": "singleSelect", "options": {"choices": [
                {"name": "Escola"},{"name": "Casa"},{"name": "Saúde"},{"name": "Lazer"},
            ]}},
            {"name": "Recorrencia",         "type": "singleSelect", "options": {"choices": [
                {"name": "Diária"},{"name": "Semanal"},{"name": "Única"},
            ]}},
        ],
    },
    {
        "nome": "Agenda_Escolar",
        "campos": [
            {"name": "Titulo",      "type": "singleLineText"},
            {"name": "Data_Prazo",  "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Tipo",        "type": "singleSelect", "options": {"choices": [
                {"name": "Prova"},{"name": "Trabalho"},{"name": "Evento"},
                {"name": "Reunião de Pais"},{"name": "Outros"},
            ]}},
            {"name": "Disciplina",  "type": "singleLineText"},
            {"name": "Status",      "type": "singleSelect", "options": {"choices": [
                {"name": "Pendente"},{"name": "Preparando"},{"name": "Concluído"},
            ]}},
            {"name": "Urgencia",    "type": "singleSelect", "options": {"choices": [
                {"name": "Alta"},{"name": "Média"},{"name": "Baixa"},
            ]}},
            {"name": "Notas",       "type": "multilineText"},
        ],
    },
]


def popular_dados_exemplo():
    """Popula tabelas com dados de exemplo para teste imediato."""
    from pyairtable import Api
    api = Api(API_KEY)

    print("\n📦 Populando dados de exemplo...")

    # Membros da família
    t_membros = api.table(BASE_ID, "Membros_Familia")
    t_membros.create({"Nome": "Joice", "Tipo": "Adulto", "Idade": 35,
                       "Pontos_XP": 0, "Nivel": "⭐ Iniciante",
                       "Avatar_Emoji": "👩‍💼", "Email_Whatsapp": os.environ.get("WHATSAPP_ADULTO_1", "")})
    t_membros.create({"Nome": "Lucas", "Tipo": "Criança", "Idade": 9,
                       "Pontos_XP": 2840, "Nivel": "🌟 Explorador",
                       "Avatar_Emoji": "🦸", "Email_Whatsapp": ""})
    t_membros.create({"Nome": "Bia", "Tipo": "Criança", "Idade": 7,
                       "Pontos_XP": 1960, "Nivel": "⭐ Iniciante",
                       "Avatar_Emoji": "🧚", "Email_Whatsapp": ""})
    print("  ✅ Membros criados")

    # Tarefas de exemplo
    t_tarefas = api.table(BASE_ID, "Tarefas_Familiares")
    from datetime import date
    hoje = date.today().isoformat()
    tarefas_ex = [
        {"Titulo_Tarefa": "Arrumar a cama", "Emoji_Icone": "🛏️", "Responsavel": "Lucas",
         "Data_Prazo": hoje, "Status": "A Fazer", "Pontos_Recompensa": 20,
         "Recompensa_Descricao": "20 min de tablet", "Categoria": "Casa", "Recorrencia": "Diária"},
        {"Titulo_Tarefa": "Lição de casa", "Emoji_Icone": "📚", "Responsavel": "Bia",
         "Data_Prazo": hoje, "Status": "A Fazer", "Pontos_Recompensa": 50,
         "Recompensa_Descricao": "Escolher história da noite", "Categoria": "Escola", "Recorrencia": "Diária"},
        {"Titulo_Tarefa": "Escovar os dentes", "Emoji_Icone": "🦷", "Responsavel": "Bia",
         "Data_Prazo": hoje, "Status": "A Fazer", "Pontos_Recompensa": 10,
         "Categoria": "Saúde", "Recorrencia": "Diária"},
    ]
    for t in tarefas_ex:
        t_tarefas.create(t)
    print("  ✅ Tarefas de exemplo criadas")


def main():
    print("🚀 Configurando Airtable — Centro de Comando")
    print(f"   Base ID: {BASE_ID}\n")

    for tabela in TABELAS:
        criar_tabela(tabela["nome"], tabela["campos"])
        time.sleep(0.5)  # Evita rate limit da API

    print("\n✅ Todas as tabelas criadas!\n")

    resp = input("Deseja popular com dados de exemplo? (s/n): ").strip().lower()
    if resp == "s":
        popular_dados_exemplo()

    print("\n🎉 Setup completo! Próximo passo:")
    print("   1. Copie o AIRTABLE_BASE_ID acima")
    print("   2. Cole no seu .env")
    print("   3. Execute: docker-compose up -d")


if __name__ == "__main__":
    main()
