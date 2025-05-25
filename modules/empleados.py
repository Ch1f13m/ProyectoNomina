from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Blueprint
from utils.db import get_db_connection
from datetime import datetime

bp = Blueprint('empleados', __name__, url_prefix='/api')

def parse_fecha(fecha_str):
    if not fecha_str:
        return None
    try:
        # Intenta parsear formato tipo 'Sat, 14 Jun 2025 00:00:00 GMT'
        return datetime.strptime(fecha_str[:16], "%a, %d %b %Y").date()
    except Exception:
        try:
            # Intenta formato 'YYYY-MM-DD'
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except Exception:
            return None

@bp.route('/empleados', methods=['GET'])
def listar_empleados():
    empresa_id = request.args.get('empresa_id', type=int)

    if not empresa_id:
        return jsonify({"error": "Falta empresa_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC Empleado.sp_listar_empleados_empresa ?", (empresa_id,))
        empleados = cursor.fetchall()
        columnas = [col[0] for col in cursor.description]
        empleados_dict = [dict(zip(columnas, fila)) for fila in empleados]
        nombre = request.args.get('nombre', type=str)
        if nombre:
            nombre = nombre.lower()
            empleados_dict = [
                emp for emp in empleados_dict
                if nombre in (emp.get('nombre_completo', '').lower())
            ]
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Error al obtener empleados"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(empleados_dict)

@bp.route('/empleados', methods=['POST'])
def crear_empleado_api():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        data = request.get_json()
        cursor.execute(
    "EXEC Empleado.sp_insertar_empleado ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?",
    (
        data['tipo_documento'],
        data['numero_documento'],
        data['primer_nombre'],
        data.get('segundo_nombre', ''),
        data['primer_apellido'],
        data.get('segundo_apellido', ''),
        parse_fecha(data['fecha_nacimiento']),
        data.get('direccion', ''),
        data.get('telefono', ''),
        data.get('email', ''),
        data['estado_civil'],
        parse_fecha(data['fecha_ingreso']),
        float(data['salario_actual']),
        1 if data.get('auxilio_transporte_aplica') else 0,
        data['empresa_id'],
        data['tipo_contrato'],
        data['cargo'],
        data['estado_contrato'],
        int(data['nivel_riesgo_arl'])
    )
)
        conn.commit()
        return jsonify({"message": "Empleado creado correctamente"}), 201

    except Exception as e:
        conn.rollback()
        if 'duplicate key' in str(e).lower():
            return jsonify({"error": "Ya existe un empleado con ese número de documento."}), 400
        print("Error al insertar empleado:", e)
        return jsonify({"error": "Error al insertar empleado"}), 500

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

@bp.route('/empleados/<int:id>', methods=['PUT'])
def actualizar_empleado(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data = request.get_json()
        print("Datos recibidos:", data)  # Log para verificar los datos recibidos

        empresa_id = data.get('empresa_id')
        if not empresa_id:
            return jsonify({"error": "Falta empresa_id"}), 400

        print("Ejecutando procedimiento almacenado...")  # Log antes de ejecutar la consulta
        cursor.execute(
            "EXEC Empleado.sp_actualizar_empleado ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?",
            (
                id,  # 1
                data['tipo_documento'],  # 2
                data['numero_documento'],  # 3
                data['primer_nombre'],  # 4
                data.get('segundo_nombre', ''),  # 5
                data['primer_apellido'],  # 6
                data.get('segundo_apellido', ''),  # 7
                parse_fecha(data['fecha_nacimiento']),  # 8
                data.get('direccion', ''),  # 9
                data.get('telefono', ''),  # 10
                data.get('email', ''),  # 11
                data['estado_civil'],  # 12
                parse_fecha(data['fecha_ingreso']),  # 13
                1 if data.get('auxilio_transporte_aplica') else 0,  # 14
                data['estado_empleo']  # 15
            )
        )
        conn.commit()
        print("Empleado actualizado correctamente.")  # Log después de la consulta
        return jsonify({"message": "Empleado actualizado correctamente"}), 200
    except Exception as e:
        conn.rollback()
        print("Error al actualizar empleado:", e)
        return jsonify({"error": f"Error al actualizar empleado: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/crear/<int:empleado_id>', methods=['GET', 'POST'])
def crear_novedad(empleado_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    dias_disponibles = 0
    try:
        cursor.execute("EXEC Novedad.sp_calcular_dias_vacaciones ?", (empleado_id,))
        resultado = cursor.fetchone()
        dias_disponibles = resultado[0] if resultado else 0
    except Exception as e:
        print("Error al obtener días disponibles:", e)
        dias_disponibles = 0

    if request.method == 'POST':
        # Soportar JSON y form-data
        if request.is_json:
            data = request.get_json()
            tipo_novedad = data.get('tipo_novedad')
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            se_paga = data.get('se_paga')
        else:
            tipo_novedad = request.form['tipo_novedad']
            fecha_inicio = request.form['fecha_inicio']
            fecha_fin = request.form['fecha_fin']
            se_paga = request.form['se_paga']

        try:
            if tipo_novedad == 'Vacaciones':
                mensaje = ''
                cursor.execute("EXEC Novedad.sp_registrar_vacacion_segura ?, ?, ?, ? OUTPUT", (empleado_id, fecha_inicio, fecha_fin, mensaje))
                # Obtener mensaje de salida
                cursor.nextset()
                mensaje = cursor.fetchone()[0] if cursor.description else 'Vacaciones registradas correctamente.'
                if "correctamente" in mensaje:
                    conn.commit()
                    if request.is_json:
                        return jsonify({'success': True, 'message': mensaje}), 200
                    flash(mensaje, 'success')
                    return redirect(url_for('empleados.listar_empleados'))
                else:
                    conn.rollback()
                    if request.is_json:
                        return jsonify({'success': False, 'message': mensaje}), 400
                    flash(mensaje, 'error')
                    return render_template('novedades_formulario.html', empleado_id=empleado_id, tipo_novedad=tipo_novedad, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, se_paga=se_paga, dias_disponibles=dias_disponibles)
            else:
                if se_paga == 'si':
                    cursor.execute('EXEC Novedad.sp_calcular_valor_novedad ?, ?, ?, ?', (empleado_id, tipo_novedad, fecha_inicio, fecha_fin))
                else:
                    cursor.execute('EXEC Novedad.sp_insertar_novedad ?, ?, ?, ?, ?', (empleado_id, tipo_novedad, fecha_inicio, fecha_fin, 0))
                conn.commit()
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Novedad registrada correctamente'}), 200
                flash("Novedad registrada correctamente", 'success')
                return redirect(url_for('empleados.listar_empleados'))
        except Exception as e:
            conn.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': f"Error al insertar novedad: {str(e)}"}), 500
            flash(f"Error al insertar novedad: {str(e)}", 'error')
            return render_template('novedades_formulario.html', empleado_id=empleado_id, tipo_novedad=tipo_novedad, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, se_paga=se_paga, dias_disponibles=dias_disponibles)

    cursor.close()
    conn.close()
    if request.is_json:
        return jsonify({'dias_disponibles': dias_disponibles})
    return render_template('novedades_formulario.html', empleado_id=empleado_id, dias_disponibles=dias_disponibles)