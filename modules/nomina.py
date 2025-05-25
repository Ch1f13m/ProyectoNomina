from flask import Blueprint, request, jsonify, session
from utils.db import get_db_connection

bp = Blueprint('nomina', __name__, url_prefix='/api/nomina')



@bp.route('/generar', methods=['POST'])
def generar_nomina():
    if 'empresa_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.get_json()
    contrato_id = data.get('contrato_id')

    if not contrato_id:
        return jsonify({'error': 'Falta contrato_id'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ejecutar SP con parámetro y OUTPUT + SELECT
        cursor.execute("""
            DECLARE @mensaje VARCHAR(255);
            EXEC Nomina.sp_calcularDetalleNomina ?, @mensaje OUTPUT;
            SELECT @mensaje AS mensaje;
        """, (contrato_id,))

        # Avanzar a los resultados hasta encontrar SELECT final
        mensaje = None
        while True:
            if cursor.description:
                row = cursor.fetchone()
            if row:
                mensaje = row[0]
                break
            if not cursor.nextset():
                break

        conn.commit()

        if mensaje:
            return jsonify({'message': mensaje}), 201
        else:
            return jsonify({'error': 'No se pudo obtener mensaje de salida'}), 500

    except Exception as e:
        import traceback
        print("Error al generar nómina:", e)
        traceback.print_exc()  # ✅ Muestra error detallado
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()




        
@bp.route('/contratos', methods=['GET'])
def listar_contratos():
    if 'empresa_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    empresa_id = session['empresa_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC Contrato.sp_listar_contratos_empresa ?", (empresa_id,))
        contratos = cursor.fetchall()
        columnas = [col[0] for col in cursor.description]
        contratos_dict = [dict(zip(columnas, fila)) for fila in contratos]
        return jsonify(contratos_dict)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Error al obtener contratos"}), 500
    finally:
        cursor.close()
        conn.close()
