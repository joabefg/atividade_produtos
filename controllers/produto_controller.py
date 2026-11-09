from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for
from database import conectar_banco

produto = Blueprint("produto_bp", __name__)

def _conectar():
    return conectar_banco(current_app.config["DATABASE"])


@produto.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "GET":
        return render_template("cadastrar.html")

    dados = request.get_json(silent=True) if request.is_json else request.form
    dados = dados or {}
    nome = str(dados.get("nome", "")).strip()
    descricao = str(dados.get("descricao", "")).strip()
    categoria = str(dados.get("categoria", "")).strip()

    try:
        preco = float(dados.get("preco", ""))
        quantidade = int(dados.get("quantidade", ""))
    except (TypeError, ValueError):
        erro = "Informe um preço e uma quantidade válidos."
        if request.is_json:
            return jsonify(erro=erro), 400
        return jsonify(erro=erro), 400

    if not nome or preco < 0 or quantidade < 0:
        erro = "Preencha o nome e use valores não negativos para preço e quantidade."
        if request.is_json:
            return jsonify(erro=erro), 400
        return jsonify(erro=erro), 400

    conexao = _conectar()
    cursor = conexao.execute(
        "INSERT INTO produtos (nome, descricao, preco, quantidade, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, quantidade, categoria),
    )
    conexao.commit()
    produto_id = cursor.lastrowid
    conexao.close()

    if request.is_json:
        return jsonify(id=produto_id, mensagem="Produto cadastrado com sucesso."), 201
    return redirect(url_for("produto_bp.listar"))


@produto.route("/api/produtos/<int:produto_id>", methods=["GET"])
def obter_produto(produto_id):
    conexao = _conectar()
    item = conexao.execute(
        "SELECT * FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()
    conexao.close()
    if item is None:
        return jsonify(erro="Produto não encontrado."), 404
    return jsonify(dict(item))


@produto.route("/editar/<int:produto_id>", methods=["GET", "POST", "PUT"])
def editar(produto_id):
    conexao = _conectar()
    produto_atual = conexao.execute(
        "SELECT * FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()
    conexao.close()
    if produto_atual is None:
        abort(404)

    if request.method == "GET":
        return render_template("cadastrar.html")

    dados = request.get_json(silent=True) if request.is_json else request.form
    dados = dados or {}
    nome = str(dados.get("nome", "")).strip()
    descricao = str(dados.get("descricao", "")).strip()
    categoria = str(dados.get("categoria", "")).strip()
    try:
        preco = float(dados.get("preco", ""))
        quantidade = int(dados.get("quantidade", ""))
    except (TypeError, ValueError):
        return jsonify(erro="Informe um preço e uma quantidade válidos."), 400

    if not nome or preco < 0 or quantidade < 0:
        return jsonify(
            erro="Preencha o nome e use valores não negativos para preço e quantidade."
        ), 400

    conexao = _conectar()
    conexao.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, quantidade = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, quantidade, categoria, produto_id),
    )
    conexao.commit()
    conexao.close()
    if request.is_json:
        return jsonify(mensagem="Produto atualizado com sucesso.")
    return redirect(url_for("produto_bp.listar"))

@produto.route("/listar", methods=["GET"])
def listar():
    conexao = _conectar()
    produtos = conexao.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    conexao.close()
    if request.args.get("formato") == "json":
        return jsonify([dict(item) for item in produtos])
    return render_template("listar.html")

@produto.route("/apagar", methods=["DELETE"])
def apagar():
    dados = request.get_json(silent=True) or {}
    try:
        produto_id = int(dados.get("id", ""))
    except (TypeError, ValueError):
        return jsonify(erro="Informe um id de produto válido."), 400

    conexao = _conectar()
    cursor = conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conexao.commit()
    conexao.close()
    if cursor.rowcount == 0:
        return jsonify(erro="Produto não encontrado."), 404
    return jsonify(mensagem="Produto excluído com sucesso.")


@produto.route("/apagar/<int:produto_id>", methods=["POST"])
def apagar_pela_tela(produto_id):
    conexao = _conectar()
    conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conexao.commit()
    conexao.close()
    return redirect(url_for("produto_bp.listar"))