from flask import Flask, render_template, request, send_from_directory
from models import db, Usuario, Apuesta
import os

app = Flask(__name__, template_folder='f1-app', static_folder='f1-app')

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pagos')
def pagos():
    return render_template('pagos.html')

@app.route('/pagar', methods=['POST'])
def pagar():
    usuario_id = request.form['usuario_id']
    monto = request.form['monto']

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return f"<h3>⚠️ Usuario con ID {usuario_id} no encontrado.</h3>"

    nueva_apuesta = Apuesta(usuario_id=usuario_id, monto=monto)
    db.session.add(nueva_apuesta)
    db.session.commit()

    return f"<h3>✅ Apuesta registrada correctamente para {usuario.nombre} (monto: ${monto})</h3>"

@app.route('/css/<path:filename>')
def css(filename):
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/img/<path:filename>')
def img(filename):
    return send_from_directory(os.path.join(app.static_folder, 'img'), filename)

if __name__ == '__main__':
    app.run(debug=True)
