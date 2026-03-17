
# ============================================================
#  IMPORTAÇÕES
# ============================================================
from flask import Flask, render_template, request, session, redirect, g
import sqlite3
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

DATABASE = "database.db"

# =========================================================================
#  Para o dropdown “Por Recurso” CONTER AS OPÇÕES E funcionar No base.html 
# =========================================================================

@app.context_processor
def inject_recursos_dropdown():
    db = get_db()
    recursos = db.execute("SELECT * FROM recursos ORDER BY nome").fetchall()
    return {"recursos_dropdown": recursos}


# ============================================================
#  DECORADOR login_required (AULA 21)
# ============================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            session["next"] = request.path
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

# ============================================================
#  DECORADOR Para o Admin
# ============================================================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")

        if session.get("perfil") != "admin":
            session["msg"] = "Acesso restrito a administradores."
            return redirect("/reservas")

        return f(*args, **kwargs)
    return wrapper




# ============================================================
#  BASE DE DADOS (Aula 22)
# ============================================================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("database.db")
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ============================================================
#  ROTAS BÁSICAS
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sobre")
def sobre():
    return render_template("sobre.html")

@app.route("/contactos")
def contactos():
    return render_template("contactos.html")


# ============================================================
#  LOGIN (AULA 19)
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("login.html", erro="Preencha todos os campos.")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user is None:
            session["msg"] = "Utilizador não encontrado. Crie a sua conta."
            return redirect("/register")


        if user["password"] != password:
            return render_template("login.html", erro="Password incorreta.")
        
    # LOGIN BEM-SUCEDIDO
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["perfil"] = user["perfil"]


        next_page = session.pop("next", None)
        if next_page:
            return redirect(next_page)

        return redirect("/area_privada")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ============================================================
#  ÁREA PRIVADA MELHORADA
# ============================================================
@app.route("/area_privada")
@admin_required
def area_privada():
    db = get_db()

    total_reservas = db.execute(
        "SELECT COUNT(*) AS total FROM reservas WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()["total"]

    total_recursos = db.execute(
        "SELECT COUNT(*) AS total FROM recursos"
    ).fetchone()["total"]

    total_users = db.execute(
        "SELECT COUNT(*) AS total FROM users"
    ).fetchone()["total"]

    return render_template(
        "area_privada.html",
        username=session["username"],
        total_reservas=total_reservas,
        total_recursos=total_recursos,
        total_users=total_users
    )


# ============================================================
#  CRUD USERS (AULA 23)
# ============================================================
@app.route("/users")
@admin_required
def users():
    db = get_db()
    rows = db.execute("SELECT * FROM users").fetchall()
    return render_template("users.html", users=rows)

@app.route("/users/create")
@admin_required
def create_users():
    return render_template("create_users.html")

@app.route("/users/create", methods=["POST"])
@admin_required
def create_users_post():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    db = get_db()
    db.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
               (username, email, password))
    db.commit()
    return redirect("/users")

@app.route("/users/edit/<int:id>")
@admin_required
def edit_user(id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    return render_template("edit_user.html", user=user)

@app.route("/users/edit/<int:id>", methods=["POST"])
@admin_required
def edit_user_atual(id):
    username = request.form.get("username")
    email = request.form.get("email")

    db = get_db()
    db.execute("UPDATE users SET username=?, email=? WHERE id=?", (username, email, id))
    db.commit()
    return redirect("/users")

@app.route("/users/delete/<int:id>", methods=["POST"])
@admin_required
def delete_user(id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (id,))
    db.commit()
    return redirect("/users")


# ============================================================
#  --- AULA 24 (VERSÃO ANTIGA — AGORA SUBSTITUÍDA) ---
#  Mantida apenas para referência, mas NÃO usada.
# ============================================================

"""
@app.route("/criar_reservas", methods=["POST"])
@login_required
def criar_reservas_antiga():
    recurso = request.form["recurso"]
    data = request.form["data"]
    hora = request.form["hora"]
    observ = request.form["observacoes"]

    db = get_db()
    db.execute(
        "INSERT INTO reservas (user_id, recurso, data, hora, observacoes) VALUES (?, ?, ?, ?, ?)",
        (session['user_id'], recurso, data, hora, observ)
    )
    db.commit()
    return redirect("/reservas")
"""
# ESTA VERSÃO NÃO FUNCIONA MAIS PORQUE A TABELA AGORA USA recurso_id


# ============================================================
#  --- AULA 25 (VERSÃO ANTIGA COM VALIDAÇÕES) ---
#  Mantida apenas para referência, mas NÃO usada.
# ============================================================

"""
@app.route("/criar-reserva", methods=["POST"])
@login_required
def criar_reserva_validacoes_antiga():
    recurso = request.form["recurso"]
    data = request.form["data"]
    hora = request.form["hora"]
    obs = request.form["observacoes"]

    if not recurso or not data or not hora:
        return render_template("criar_reserva.html", erro="Todos os campos são obrigatórios")

    if data < str(date.today()):
        return render_template("criar_reserva.html", erro="Não podes reservar para uma data passada")

    db = get_db()
    conflito = db.execute(
        "SELECT * FROM reservas WHERE recurso = ? AND data = ? AND hora = ?",
        (recurso, data, hora)
    ).fetchone()

    if conflito:
        return render_template("criar_reserva.html", erro="Este horário já está reservado")

    db.execute(
        "INSERT INTO reservas (user_id, recurso, data, hora, observacoes) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], recurso, data, hora, obs)
    )
    db.commit()
    return redirect("/reservas")
"""
# ESTA VERSÃO NÃO FUNCIONA MAIS PORQUE A TABELA AGORA USA recurso_id


# ============================================================
#  AULA 26 — VERSÃO FINAL (ATIVA)
#  CRUD COMPLETO DE RESERVAS COM recurso_id + VALIDAÇÕES
# ============================================================

# --- GET: Formulário com dropdown ---
@app.route("/criar-reserva")
@login_required
def criar_reserva_form():
    db = get_db()
    recursos = db.execute("SELECT * FROM recursos").fetchall()
    return render_template("criar_reserva.html", recursos=recursos)


# ============================================================
# --- POST: Criar reserva com validações ---
# ============================================================
@app.route("/criar-reserva", methods=["POST"])
@login_required
def criar_reserva():
    recurso_id = request.form["recurso_id"]
    data = request.form["data"]
    hora = request.form["hora"]
    obs = request.form["observacoes"]

    # Campos obrigatórios
    if not recurso_id or not data or not hora:
        db = get_db()
        recursos = db.execute("SELECT * FROM recursos").fetchall()
        return render_template("criar_reserva.html", recursos=recursos,
                               erro="Todos os campos são obrigatórios")

    # Data no passado
    if data < str(date.today()):
        db = get_db()
        recursos = db.execute("SELECT * FROM recursos").fetchall()
        return render_template("criar_reserva.html", recursos=recursos,
                               erro="Não podes reservar para uma data passada")

    db = get_db()

    # Conflito de horário
    conflito = db.execute(
        "SELECT * FROM reservas WHERE recurso_id = ? AND data = ? AND hora = ?",
        (recurso_id, data, hora)
    ).fetchone()

    if conflito:
        recursos = db.execute("SELECT * FROM recursos").fetchall()
        return render_template("criar_reserva.html", recursos=recursos,
                               erro="Este horário já está reservado")

    # Inserir reserva
    db.execute(
        "INSERT INTO reservas (user_id, recurso_id, data, hora, observacoes) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], recurso_id, data, hora, obs)
    )
    db.commit()

    session["msg"] = "Reserva criada com sucesso!" #feedback (Gamma 27/28)
    return redirect("/reservas")

   

"""
# ============================================================
# --- LISTAR RESERVAS (JOIN) ---versão antiga
# ============================================================
@app.route("/reservas")
@login_required
def reservas():
    db = get_db()
    rows = db.execute(
       
        SELECT reservas.*, recursos.nome AS recurso_nome
        FROM reservas
        JOIN recursos ON reservas.recurso_id = recursos.id
        WHERE reservas.user_id = ?
        ORDER BY data, hora
        
        (session["user_id"],)
    ).fetchall()

    return render_template("reservas.html", reservas=rows)
"""

# ===============================================================
# --- GAMMA 27 LISTAR RESERVAS (JOIN) + FILTROS --- Versão ATIVA
# ===============================================================
@app.route("/reservas")
@login_required
def reservas():
    recurso_id = request.args.get("recurso_id")
    data = request.args.get("data")

    query = """
        SELECT reservas.*, recursos.nome AS recurso_nome
        FROM reservas
        JOIN recursos ON reservas.recurso_id = recursos.id
        WHERE reservas.user_id = ?
    """
    params = [session["user_id"]]

    if recurso_id:
        query += " AND reservas.recurso_id = ?"
        params.append(recurso_id)

    if data:
        query += " AND reservas.data = ?"
        params.append(data)

    query += " ORDER BY data, hora"

    db = get_db()
    reservas_rows = db.execute(query, params).fetchall()
    recursos_rows = db.execute("SELECT * FROM recursos").fetchall()

    return render_template("reservas.html",
                           reservas=reservas_rows,
                           recursos=recursos_rows)




# ============================================================
# --- EDITAR RESERVA (GET) ---
# ============================================================
@app.route("/editar-reserva/<int:id>")
@login_required
def editar_reserva(id):
    db = get_db()

    reserva = db.execute(
        "SELECT * FROM reservas WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    ).fetchone()

    recursos = db.execute("SELECT * FROM recursos").fetchall()

    if reserva is None:
        return redirect("/reservas")

    return render_template("editar_reserva.html", r=reserva, recursos=recursos)


# ============================================================
# --- EDITAR RESERVA (POST) ---
# ============================================================
@app.route("/editar-reserva/<int:id>", methods=["POST"])
@login_required
def atualizar_reserva(id):
    recurso_id = request.form["recurso_id"]
    data = request.form["data"]
    hora = request.form["hora"]
    obs = request.form["observacoes"]

    db = get_db()

    # Data no passado
    if data < str(date.today()):
        recursos = db.execute("SELECT * FROM recursos").fetchall()
        return render_template("editar_reserva.html", r={"id": id, "recurso_id": recurso_id,
                                                         "data": data, "hora": hora,
                                                         "observacoes": obs},
                               recursos=recursos,
                               erro="Não podes reservar para uma data passada")

    # Conflito (exceto a própria reserva)
    conflito = db.execute(
        "SELECT * FROM reservas WHERE recurso_id = ? AND data = ? AND hora = ? AND id != ?",
        (recurso_id, data, hora, id)
    ).fetchone()

    if conflito:
        recursos = db.execute("SELECT * FROM recursos").fetchall()
        return render_template("editar_reserva.html", r={"id": id, "recurso_id": recurso_id,
                                                         "data": data, "hora": hora,
                                                         "observacoes": obs},
                               recursos=recursos,
                               erro="Este horário já está reservado")

    # Atualizar
    db.execute(
        "UPDATE reservas SET recurso_id = ?, data = ?, hora = ?, observacoes = ? WHERE id = ? AND user_id = ?",
        (recurso_id, data, hora, obs, id, session["user_id"])
    )
    db.commit()
    session["msg"] = "Reserva atualizada com sucesso!" #feedback (Gamma 27/28)
    return redirect("/reservas")



# ============================================================
# --- APAGAR RESERVA ---
# ============================================================
@app.route("/apagar-reserva/<int:id>", methods=["POST"])
@login_required
def apagar_reserva(id):
    db = get_db()
    db.execute(
        "DELETE FROM reservas WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    )
    

    db.commit()
    session["msg"] = "Reserva eliminada com sucesso!" #feedback (Gamma 27/28)
    return redirect("/reservas")



# ============================================================
#  GAMMA 28 - RELATÓRIO POR RECURSO
# ============================================================
@app.route("/relatorio/recurso/<int:id>")
@login_required
def relatorio_recurso(id):
    db = get_db()
    rows = db.execute("""
        SELECT reservas.*, recursos.nome AS recurso_nome, users.username
        FROM reservas
        JOIN recursos ON reservas.recurso_id = recursos.id
        JOIN users ON reservas.user_id = users.id
        WHERE reservas.recurso_id = ?
        ORDER BY data, hora
    """, (id,)).fetchall()

    return render_template("relatorio_recurso.html", reservas=rows)


# ============================================================
#  GAMMA 28 - RELATÓRIO POR DATA
# ============================================================
@app.route("/relatorio/data")
@login_required
def relatorio_data():
    data = request.args.get("data")
    reservas_rows = []

    if data:
        db = get_db()
        reservas_rows = db.execute("""
            SELECT reservas.*, recursos.nome AS recurso_nome
            FROM reservas
            JOIN recursos ON reservas.recurso_id = recursos.id
            WHERE reservas.data = ?
            ORDER BY hora
        """, (data,)).fetchall()

    return render_template("relatorio_data.html",
                           reservas=reservas_rows,
                           data=data)


# ============================================================
#  GAMMA 28 - RELATÓRIO: MINHAS RESERVAS
# ============================================================
@app.route("/relatorio/minhas")
@login_required
def minhas_reservas():
    db = get_db()
    rows = db.execute("""
        SELECT reservas.*, recursos.nome AS recurso_nome
        FROM reservas
        JOIN recursos ON reservas.recurso_id = recursos.id
        WHERE reservas.user_id = ?
        ORDER BY data, hora
    """, (session["user_id"],)).fetchall()

    return render_template("relatorio_minhasR.html", reservas=rows)


# ======================================================================
#  ROTA CRIAR UTILZADOR CASO NÃO EXISTA - USER AO AUTENTICAR-SE
#  MELHORAR PROJETO
# ======================================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()

        # verificar se já existe
        existe = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existe:
            return render_template("registerUser.html", erro="O utilizador já existe.")

        db.execute("""
            INSERT INTO users (username, email, password, perfil)
            VALUES (?, ?, ?, 'user')
        """, (username, email, password))

        db.commit()

        session["msg"] = "Conta criada com sucesso! Já pode fazer login."
        return redirect("/login")
    return render_template("registerUser.html")


# ============================================================
#  EXECUTAR A APLICAÇÃO
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
