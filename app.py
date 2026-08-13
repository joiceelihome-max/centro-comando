"""
app.py — Centro de Comando Familiar & Empresarial
"""
import os, logging
from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()

from modules.financeiro      import bp as financeiro_bp
from modules.administrativo  import bp as administrativo_bp
from modules.familiar        import bp as familiar_bp

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.register_blueprint(financeiro_bp)
app.register_blueprint(administrativo_bp)
app.register_blueprint(familiar_bp)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "servico": "Centro de Comando", "versao": "1.0.0"})

@app.route("/rotas")
def listar_rotas():
    rotas = [{"rota": str(r), "metodos": sorted([m for m in r.methods if m not in ("HEAD","OPTIONS")])}
             for r in app.url_map.iter_rules() if r.endpoint != "static"]
    return jsonify({"total": len(rotas), "rotas": sorted(rotas, key=lambda x: x["rota"])})

@app.errorhandler(404)
def not_found(e): return jsonify({"status": "error", "message": "Rota não encontrada"}), 404
@app.errorhandler(500)
def server_error(e): return jsonify({"status": "error", "message": "Erro interno"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
