
from dashboard import Dashboard
from db_con import database_connection, get_db_params
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text




# Get database parameters from environment (works in Docker and local)
server, database, username, password, driver = get_db_params()
print(f"Connecting to database: {database} on server: {server} with user: {username}")
engine = database_connection(server, database, username, password, driver)  # Conexão com o banco de dados
server = Flask(__name__)  # Inicializa o servidor Flask
server.secret_key = 'secret_key'  # Chave secreta para sessões
dashboard = Dashboard(server, engine).app  # Inicializa o dashboard e vincula ao servidor Flask

@server.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        with engine.connect() as conn:
            user = conn.execute(
                text("SELECT * FROM USERS_TABLE WHERE nome = :usuario"),
                {"usuario": usuario}
            ).fetchone()
        if user and check_password_hash(user.senha, senha):
            session["user_id"] = user.id
            session["nome"] = user.nome
            return redirect(url_for("dashboard"))   
        else:
            # Aqui já cria o "warning" que será mostrado no HTML
            flash("⚠️ Usuário ou senha inválidos.", "warning")

    return render_template("login.html")


# Página protegida
@server.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("/dashboard/"))


# Logout
@server.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@server.route('/home')
def homepage():
    return render_template('home.html')


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=935,debug=True)
 # Executa o servidor Flask com o dashboard integrado