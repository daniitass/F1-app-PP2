from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Relación con apuestas
    apuestas = db.relationship('Apuesta', backref='usuario', lazy=True)

class Apuesta(db.Model):
    __tablename__ = 'apuestas'
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    resultado = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
