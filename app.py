from pathlib import Path

from flask import Flask, redirect, url_for
from database import inicializar_banco
from controllers.produto_controller import produto

app = Flask(__name__)
app.config["DATABASE"] = str(Path(app.root_path) / "produtos.db")

inicializar_banco(app.config["DATABASE"])

app.register_blueprint(produto)

@app.route("/", methods=["GET"])
def inicio():
    return redirect(url_for("produto_bp.listar"))

if __name__ == '__main__':
    app.run(debug=True)