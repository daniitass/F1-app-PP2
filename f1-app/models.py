from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # IMPORTANTE: NO agregar apellido ni fecha_nacimiento,
    # porque tu base y tu proyecto nunca los definieron.

class Apuesta(db.Model):
    __tablename__ = "apuestas"

    id = db.Column(db.Integer, primary_key=True)
    piloto = db.Column(db.String(100), nullable=False)
    monto = db.Column(db.Float, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    usuario = db.relationship("User")
