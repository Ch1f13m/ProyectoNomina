from flask import Blueprint, request, redirect, url_for, render_template, session,jsonify
from utils.db import get_db_connection

bp = Blueprint('contratos', __name__, url_prefix='/api')


@bp.route('/nuevo', methods=['POST', 'OPTIONS'])
def crear_contrato():

    if request.method == 'OPTIONS':
        return jsonify({'message': 'Preflight OK'}), 200

   
    if 'empresa_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.json 

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "EXEC Contrato.sp_insertar_contrato ?, ?, ?, ?, ?, ?, ?, ?, ?",
            (
                int(data['empleado_id']),
                int(session['empresa_id']),
                data['tipo_contrato'],
                data['fecha_inicio'],
                data.get('fecha_fin', None),
                data['cargo'],
                int(data['nivel_riesgo_arl']),
                float(data['salario_contrato']),
                data['estado_contrato']
            )
        )
        conn.commit()
        return jsonify({'message': 'Contrato creado exitosamente'}), 201
    except Exception as e:
        print("Error al insertar contrato:", e)
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@bp.route('/contratos', methods=['GET'])
def listar_contratos():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Cambia aquí: lee empresa_id del parámetro GET
        empresa_id = request.args.get('empresa_id', type=int)
        if empresa_id is not None:
            cursor.execute("EXEC Contrato.sp_listar_contratos_empresa ?", (empresa_id,))
            contratos = cursor.fetchall()
            columnas = [col[0] for col in cursor.description]
            contratos_dict = [dict(zip(columnas, fila)) for fila in contratos]
        else:
            return jsonify({"error": "No autorizado"}), 401
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Error al obtener contratos"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(contratos_dict)

@bp.route('/contratos/<int:contrato_id>', methods=['PUT'])
def actualizar_contrato(contrato_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "EXEC Contrato.sp_actualizar_contrato ?, ?, ?, ?, ?, ?",
            (
                contrato_id,
                data['tipo_contrato'],
                data.get('fecha_fin', None),
                float(data['salario_contrato']),
                int(data['nivel_riesgo_arl']),
                data['estado_contrato']
            )
        )
        conn.commit()
        return jsonify({"message": "Contrato actualizado correctamente"})
    except Exception as e:
        print("Error al actualizar contrato:", e)
        conn.rollback()
        return jsonify({"error": "Error al actualizar contrato"}), 500
    finally:
        cursor.close()
        conn.close()
        
@bp.route('/contratos/<int:contrato_id>', methods=['GET'])
def obtener_contrato(contrato_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Contrato WHERE contrato_id = ?", (contrato_id,))
        contrato = cursor.fetchone()
        if contrato:
            columnas = [col[0] for col in cursor.description]
            contrato_dict = dict(zip(columnas, contrato))
            return jsonify(contrato_dict)
        else:
            return jsonify({"error": "Contrato no encontrado"}), 404
    except Exception as e:
        print("Error al obtener contrato:", e)
        return jsonify({"error": "Error al obtener contrato"}), 500
    finally:
        cursor.close()
        conn.close()
        
@bp.route('/empleados/<int:id>', methods=['GET'])
def obtener_empleado(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC Empleado.sp_obtener_empleado ?", (id,))
        empleado = cursor.fetchone()
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        columnas = [col[0] for col in cursor.description]
        empleado_dict = dict(zip(columnas, empleado))
        return jsonify(empleado_dict)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Error al obtener empleado"}), 500
    finally:
        cursor.close()
        conn.close()
        
