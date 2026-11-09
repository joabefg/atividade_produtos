from html import escape
from math import isfinite
from pathlib import Path

from flask import Blueprint, Response, redirect, request, url_for

from database import CAMINHO_BANCO, conectar_banco

produto_bp = Blueprint("estoque", __name__)
PASTA_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def _resposta_html(nome_template, substituicoes=None, status=200):
    pagina = (PASTA_TEMPLATES / nome_template).read_text(encoding="utf-8")
    for marcador, valor in (substituicoes or {}).items():
        pagina = pagina.replace(marcador, valor)
    return Response(pagina, status=status, mimetype="text/html")


@produto_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "GET":
        return _resposta_html("cadastrar.html")

    nome = request.form.get("nome", "").strip()
    descricao = request.form.get("descricao", "").strip()
    categoria = request.form.get("categoria", "").strip()

    try:
        preco = float(request.form.get("preco", ""))
        quantidade = int(request.form.get("quantidade", ""))
        if (
            not nome
            or len(nome) > 100
            or len(categoria) > 50
            or not isfinite(preco)
            or preco < 0
            or quantidade < 0
        ):
            raise ValueError
    except ValueError:
        return _resposta_html(
            "cadastrar.html",
            {"<!-- MENSAGEM -->": "Preencha os campos corretamente."},
            status=400,
        )

    conexao = conectar_banco(CAMINHO_BANCO)
    try:
        conexao.execute(
            """
            INSERT INTO produtos (nome, descricao, preco, quantidade, categoria)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nome, descricao or None, preco, quantidade, categoria or None),
        )
        conexao.commit()
    finally:
        conexao.close()

    return redirect(url_for("estoque.listar"))


@produto_bp.route("/listar", methods=["GET"])
def listar():
    conexao = conectar_banco(CAMINHO_BANCO)
    try:
        produtos = conexao.execute(
            """
            SELECT id, nome, preco, descricao, quantidade, categoria
            FROM produtos
            ORDER BY id
            """
        ).fetchall()
    finally:
        conexao.close()

    if produtos:
        linhas = "".join(
            "<tr>"
            f"<td>{escape(str(produto['nome']))}</td>"
            f"<td>R$ {float(produto['preco']):.2f}</td>"
            f"<td>{escape(str(produto['descricao'] or '-'))}</td>"
            f"<td>{produto['quantidade']}</td>"
            f"<td>{escape(str(produto['categoria'] or '-'))}</td>"
            "<td>"
            f'<form action="/apagar/{produto["id"]}" method="post">'
            '<button type="submit">Excluir</button>'
            "</form>"
            "</td>"
            "</tr>"
            for produto in produtos
        )
    else:
        linhas = '<tr><td colspan="6">Nenhum produto cadastrado.</td></tr>'

    return _resposta_html("listar.html", {"<!-- PRODUTOS -->": linhas})


@produto_bp.route("/apagar/<int:produto_id>", methods=["POST"])
def apagar(produto_id):
    conexao = conectar_banco(CAMINHO_BANCO)
    try:
        cursor = conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conexao.commit()
    finally:
        conexao.close()

    if cursor.rowcount == 0:
        return Response("Produto não encontrado.", status=404, mimetype="text/plain")

    return redirect(url_for("estoque.listar"))
