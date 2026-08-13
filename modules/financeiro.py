"""
modules/financeiro.py — Módulo Financeiro
Extração de faturas via IA, geração de QR Code Pix, fluxo de caixa
"""
import os, json, base64, logging, qrcode, io
from datetime import datetime
from flask import Blueprint, request
import anthropic
from config import get_table, requer_auth, resposta, erro

logger = logging.getLogger(__name__)
bp     = Blueprint("financeiro", __name__, url_prefix="/financeiro")
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

PROMPT_EXTRACAO = """Analise o documento fiscal e extraia SOMENTE este JSON válido:
{
  "item": "descrição do serviço ou produto",
  "valor": 0.00,
  "data_vencimento": "YYYY-MM-DD",
  "codigo_pix": "código EMV completo ou string vazia",
  "categoria": "Moradia|Alimentação|Saúde|Educação|Transporte|Lazer|Empresarial|Outros",
  "fornecedor": "nome da empresa"
}
Regras: valor=número decimal sem R$, data=YYYY-MM-DD ou null, sem markdown."""


def extrair_dados_ia(arquivo_b64: str, mime_type: str) -> dict:
    try:
        bloco = (
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": arquivo_b64}}
            if mime_type == "application/pdf"
            else {"type": "image",    "source": {"type": "base64", "media_type": mime_type, "data": arquivo_b64}}
        )
        resp = client.messages.create(
            model="claude-opus-4-5", max_tokens=800,
            messages=[{"role": "user", "content": [bloco, {"type": "text", "text": PROMPT_EXTRACAO}]}],
        )
        texto = resp.content[0].text.strip().lstrip("```json").lstrip("```").rstrip("```")
        return json.loads(texto)
    except Exception as e:
        logger.error(f"Erro extração IA: {e}")
        return {"erro": True, "detalhes": str(e)}


def gerar_qrcode_b64(codigo_pix: str) -> str:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(codigo_pix)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@bp.route("/extrair-fatura", methods=["POST"])
@requer_auth
def extrair_fatura():
    body       = request.get_json(silent=True) or {}
    arq_b64    = body.get("arquivo_base64")
    mime_type  = body.get("mime_type", "image/png")
    if not arq_b64:
        return erro("Campo 'arquivo_base64' obrigatório", 400)

    tabela = get_table("Faturas_Recibos")
    tmp = tabela.create({"IA_Status": "Processando", "Item_Descricao": "Aguardando IA..."})

    dados = extrair_dados_ia(arq_b64, mime_type)
    if dados.get("erro"):
        tabela.update(tmp["id"], {"IA_Status": "Erro"})
        return erro(f"Falha IA: {dados.get('detalhes')}", 422)

    qr_b64 = None
    if dados.get("codigo_pix"):
        try:   qr_b64 = gerar_qrcode_b64(dados["codigo_pix"])
        except Exception as e: logger.warning(f"QR Code falhou: {e}")

    tabela.delete(tmp["id"])
    campos = {
        "Item_Descricao":   dados.get("item") or "Não identificado",
        "Valor":            float(dados.get("valor") or 0),
        "Data_Vencimento":  dados.get("data_vencimento"),
        "Codigo_Pix_Bruto": dados.get("codigo_pix") or "",
        "Categoria":        dados.get("categoria") or "Outros",
        "Status_Pagamento": "Pendente",
        "IA_Status":        "Concluído",
        "QR_Code_URL":      f"data:image/png;base64,{qr_b64}" if qr_b64 else "",
    }
    reg = tabela.create({k: v for k, v in campos.items() if v is not None})
    return resposta(data={"id": reg["id"], "item": dados.get("item"),
                          "valor": dados.get("valor"), "vencimento": dados.get("data_vencimento"),
                          "tem_qr": qr_b64 is not None})


@bp.route("/gerar-qrcode", methods=["POST"])
@requer_auth
def gerar_qrcode():
    codigo = (request.get_json(silent=True) or {}).get("codigo_pix", "")
    if not codigo: return erro("'codigo_pix' obrigatório", 400)
    try:
        return resposta(data={"qr_base64": gerar_qrcode_b64(codigo), "mime": "image/png"})
    except Exception as e:
        return erro(str(e))


@bp.route("/fluxo-de-caixa", methods=["GET"])
@requer_auth
def fluxo_de_caixa():
    mes      = request.args.get("mes", datetime.now().strftime("%Y-%m"))
    registros = get_table("Faturas_Recibos").all(formula=f"{{Mes_Referencia}}='{mes}'")
    pendentes = [r for r in registros if r["fields"].get("Status_Pagamento") == "Pendente"]
    pagos     = [r for r in registros if r["fields"].get("Status_Pagamento") == "Pago"]
    return resposta(data={
        "mes": mes,
        "total_despesas": round(sum(r["fields"].get("Valor", 0) for r in registros), 2),
        "total_pendente": round(sum(r["fields"].get("Valor", 0) for r in pendentes), 2),
        "total_pago":     round(sum(r["fields"].get("Valor", 0) for r in pagos), 2),
        "proximos_vencimentos": [
            {"item": r["fields"].get("Item_Descricao"), "valor": r["fields"].get("Valor"),
             "vencimento": r["fields"].get("Data_Vencimento")}
            for r in sorted(pendentes, key=lambda x: x["fields"].get("Data_Vencimento", ""))[:5]
        ],
    })


@bp.route("/marcar-pago/<record_id>", methods=["PATCH"])
@requer_auth
def marcar_pago(record_id: str):
    try:
        reg = get_table("Faturas_Recibos").update(record_id, {
            "Status_Pagamento": "Pago",
            "Data_Pagamento":   datetime.now().strftime("%Y-%m-%d"),
        })
        return resposta(data={"id": reg["id"]}, message="Marcada como paga")
    except Exception as e:
        return erro(str(e))
