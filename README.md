# ⚡ Centro de Comando Familiar & Empresarial

Backend Python com IA para gestão financeira, administrativa e familiar.

## Stack
- **Backend**: Python 3.12 + Flask
- **IA**: Anthropic Claude
- **Banco**: Airtable
- **Automações**: n8n (self-hosted no Railway)
- **Deploy**: Railway

## Rotas principais
| Módulo | Rota | Método |
|---|---|---|
| Health | `/health` | GET |
| Financeiro | `/financeiro/extrair-fatura` | POST |
| Financeiro | `/financeiro/fluxo-de-caixa` | GET |
| Administrativo | `/administrativo/processar-email` | POST |
| Familiar | `/familiar/briefing-diario` | POST |
| Familiar | `/familiar/ranking` | GET |

## Deploy rápido
1. Fork este repositório
2. Conecte ao Railway
3. Configure as variáveis de ambiente (veja `.env.example`)
4. Deploy automático via `railway.toml`
