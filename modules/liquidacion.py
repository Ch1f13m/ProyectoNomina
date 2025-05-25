from flask import Blueprint, request, jsonify, session
from utils.db import get_db_connection  # Asegúrate de tener este archivo

bp = Blueprint('liquidacion', __name__, url_prefix='/api/liquidaciones')


@bp.route('/generar', methods=['POST'])
def generar_liquidacion():
    if 'empresa_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.get_json()
    contrato_id = data.get('contrato_id')

    if not contrato_id:
        return jsonify({'error': 'Falta contrato_id'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DECLARE @mensaje VARCHAR(255);
            EXEC Nomina.sp_liquidar_contrato ?, @mensaje OUTPUT;
            SELECT @mensaje;
        """, contrato_id)

        mensaje = cursor.fetchone()[0]
        conn.commit()

        return jsonify({'message': mensaje}), 201

    except Exception as e:
        print("Error al generar liquidación:", e)
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()
