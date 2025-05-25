from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
from utils.db import get_db_connection
from flask_cors import CORS
from modules.empleados import bp as empleados_bp
from modules.novedades import bp as novedades_bp
from modules.contratos import bp as contratos_bp  
from modules.nomina import bp as nomina_bp
from modules.liquidacion import bp as liquidacion_bp


app = Flask(__name__)
app.secret_key = 'supersecretkey'  
CORS(app, supports_credentials=True)

CORS(app)

app.register_blueprint(empleados_bp)
app.register_blueprint(novedades_bp)
app.register_blueprint(contratos_bp)
app.register_blueprint(nomina_bp)
app.register_blueprint(liquidacion_bp)

CORS(app, supports_credentials=True)

@app.route('/api/login', methods=['POST'])
def api_login():
    from flask import request, jsonify, session  
    data = request.get_json()
    nit = data.get('nit')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("EXEC Empresa.sp_login_empresa ?, ?", (nit, password))
        empresa = cursor.fetchone()

        if empresa:
            session['empresa_id'] = empresa[0]  
            return jsonify({
                'success': True,
                'empresa_id': empresa[0],        
                'nit': empresa[1],               
                'razon_social': empresa[2],      
                'email': empresa[3],             
                'telefono': empresa[4]           
        }), 200
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401

    except Exception as e:
        print("Error en login:", e)  
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/mi_cuenta', methods=['GET', 'POST'])
def mi_cuenta():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            data = request.get_json()
            empresa_id = data.get('empresa_id')
            razon_social = data.get('razon_social')
            email = data.get('email')
            telefono = data.get('telefono')
            contrasena = data.get('contrasena')

            if not empresa_id:
                return jsonify({'error': 'Falta empresa_id'}), 400

            cursor.execute("EXEC Empresa.sp_actualizar_empresa ?, ?, ?, ?, ?",
                           (empresa_id, razon_social, email, telefono, contrasena))
            conn.commit()
            return jsonify({'message': 'Datos actualizados correctamente'}), 200

        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500

        finally:
            cursor.close()
            conn.close()
            


if __name__ == '__main__':
    app.run(debug=True)
