from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta_azul'

def get_db_connection():
    conn = sqlite3.connect('eco_reto_azul.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS acciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            impacto TEXT NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
        )
    ''')
   
    try:
        conn.execute("INSERT INTO usuarios (usuario, password) VALUES ('estudiante', '1234')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE usuario = ? AND password = ?', (usuario, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['usuario'] = user['usuario']
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos')
            
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    acciones = conn.execute('SELECT * FROM acciones WHERE id_usuario = ? ORDER BY fecha DESC', (session['user_id'],)).fetchall()
    total_acciones = len(acciones)
    conn.close()
    
    return render_template('dashboard.html', acciones=acciones, total_acciones=total_acciones)

@app.route('/nueva-accion', methods=['GET', 'POST'])
def nueva_accion():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        tipo = request.form['tipo']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha']
        impacto = request.form['impacto']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO acciones (id_usuario, tipo, descripcion, fecha, impacto) VALUES (?, ?, ?, ?, ?)',
                     (session['user_id'], tipo, descripcion, fecha, impacto))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    return render_template('nueva_accion.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_accion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    accion = conn.execute('SELECT * FROM acciones WHERE id = ? AND id_usuario = ?', (id, session['user_id'])).fetchone()
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha']
        impacto = request.form['impacto']
        
        conn.execute('UPDATE acciones SET tipo = ?, descripcion = ?, fecha = ?, impacto = ? WHERE id = ?',
                     (tipo, descripcion, fecha, impacto, id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    conn.close()
    return render_template('editar_accion.html', accion=accion)

@app.route('/detalle/<int:id>')
def detalle_accion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    accion = conn.execute('SELECT * FROM acciones WHERE id = ? AND id_usuario = ?', (id, session['user_id'])).fetchone()
    conn.close()
    
    return render_template('detalle_accion.html', accion=accion)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_accion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM acciones WHERE id = ? AND id_usuario = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)