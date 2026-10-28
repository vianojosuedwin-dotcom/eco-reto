import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'clave_secreta_azul'

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url, sslmode='require', cursor_factory=psycopg2.extras.DictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS acciones (
            id SERIAL PRIMARY KEY,
            id_usuario INTEGER,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            impacto TEXT NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
   
    try:
        cur.execute("INSERT INTO usuarios (usuario, password) VALUES ('estudiante', '1234')")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM usuarios WHERE usuario = %s AND password = %s', (usuario, password))
        user = cur.fetchone()
        cur.close()
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
    cur = conn.cursor()
    cur.execute('SELECT * FROM acciones WHERE id_usuario = %s ORDER BY fecha DESC', (session['user_id'],))
    acciones = cur.fetchall()
    total_acciones = len(acciones)
    cur.close()
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
        cur = conn.cursor()
        cur.execute('INSERT INTO acciones (id_usuario, tipo, descripcion, fecha, impacto) VALUES (%s, %s, %s, %s, %s)',
                    (session['user_id'], tipo, descripcion, fecha, impacto))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('dashboard'))
        
    return render_template('nueva_accion.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_accion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM acciones WHERE id = %s AND id_usuario = %s', (id, session['user_id']))
    accion = cur.fetchone()
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha']
        impacto = request.form['impacto']
        
        cur.execute('UPDATE acciones SET tipo = %s, descripcion = %s, fecha = %s, impacto = %s WHERE id = %s',
                    (tipo, descripcion, fecha, impacto, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('dashboard'))
        
    cur.close()
    conn.close()
    return render_template('editar_accion.html', accion=accion)

@app.route('/detalle/<int:id>')
def detalle_accion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM acciones WHERE id = %s AND id_usuario = %s', (id, session['user_id']))
    accion = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('detalle_accion.html', accion=accion)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_accion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM acciones WHERE id = %s AND id_usuario = %s', (id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
