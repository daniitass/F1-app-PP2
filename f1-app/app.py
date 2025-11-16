from flask import Flask, render_template, request, redirect, session, flash, url_for
from models import db, User, Apuesta
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# -------- CONFIG BASE DE DATOS --------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "database.db")
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# -------- RUTAS --------

# Ruta principal (INDEX)
@app.route("/")
def home():
    return render_template("index.html")

# Alias para que {{ url_for('index') }} siga funcionando
@app.route("/index")
def index():
    return redirect("/")


# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/apuestas")

        flash("Email o contraseña incorrectos", "error")

    return render_template("log.html")


# -------- REGISTRO --------
# -------- REGISTRO --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Campos que tu modelo SI puede guardar
        nombre = request.form["nombre"]
        email = request.form["email"]
        password_raw = request.form["password"]
        confirmar = request.form["confirmar_password"]

        # Validar contraseñas
        if password_raw != confirmar:
            flash("Las contraseñas no coinciden", "error")
            return redirect("/register")

        # Validar email único
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("El email ya está registrado", "error")
            return redirect("/register")

        # Hashear contraseña
        password_hash = generate_password_hash(password_raw)

        # Crear usuario SOLO con campos válidos del modelo
        user = User(
            nombre=nombre,
            email=email,
            password=password_hash
        )

        db.session.add(user)
        db.session.commit()

        flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect("/login")

    return render_template("registro.html")



# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------- APUESTAS --------
@app.route("/apuestas", methods=["GET", "POST"])
def apuestas():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        piloto = request.form["piloto"]
        monto = request.form["monto"]

        apuesta = Apuesta(
            piloto=piloto,
            monto=monto,
            usuario_id=session["user_id"]
        )

        db.session.add(apuesta)
        db.session.commit()

        return redirect("/mis_apuestas")

    return render_template("apuestas.html")


# -------- MIS APUESTAS --------
@app.route("/mis_apuestas")
def mis_apuestas():
    if "user_id" not in session:
        return redirect("/login")

    apuestas = Apuesta.query.filter_by(usuario_id=session["user_id"]).all()
    return render_template("mis_apuestas.html", apuestas=apuestas)


if __name__ == "__main__":
    app.run(debug=True)
