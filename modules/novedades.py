from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.db import get_db_connection

bp = Blueprint('novedades', __name__, url_prefix='/novedades')

@bp.route('/')
def listar_novedades():
    conn = get_db_connection()
    cursor = conn.cursor()

    nombre = request.args.get('nombre')
    tipo = request.args.get('tipo')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    # Convertir strings vacíos a None para que el procedure funcione correctamente
    nombre = nombre if nombre not in (None, '', 'null') else None
    tipo = tipo if tipo not in (None, '', 'null') else None
    fecha_inicio = fecha_inicio if fecha_inicio not in (None, '', 'null') else None
    fecha_fin = fecha_fin if fecha_fin not in (None, '', 'null') else None

    cursor.execute("EXEC Novedad.sp_filtrar_novedades_laborales ?, ?, ?, ?", (
        nombre, tipo, fecha_inicio, fecha_fin
    ))
    novedades = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    cursor.close()
    conn.close()

    # Si la petición es AJAX/JSON, devolver JSON
    if request.accept_mimetypes['application/json'] or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([dict(zip(columns, row)) for row in novedades])
    # Si no, renderizar la plantilla (legacy)
    return render_template('novedades_listado.html', novedades=novedades)

@bp.route('/eliminar/<int:novedad_id>', methods=['POST'])
def eliminar_novedad(novedad_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("EXEC Novedad.sp_eliminar_novedad_laboral ?", (novedad_id,))
        conn.commit()
        flash(" Novedad eliminada correctamente", 'success')
    except Exception as e:
        conn.rollback()
        flash(f" Error al eliminar la novedad: {str(e)}", 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('novedades.listar_novedades'))

@bp.route('/editar/<int:novedad_id>', methods=['GET', 'POST'])
def editar_novedad(novedad_id):
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        # Soportar JSON y form-data
        if request.is_json:
            data = request.get_json()
            tipo_novedad = data.get('tipo_novedad')
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            valor = data.get('valor_pagado', 0)
        else:
            tipo_novedad = request.form['tipo_novedad']
            fecha_inicio = request.form['fecha_inicio']
            fecha_fin = request.form['fecha_fin']
            valor = request.form.get('valor_pagado', 0)
        try:
            cursor.execute('EXEC Novedad.sp_actualizar_novedad ?, ?, ?, ?, ?', (
                novedad_id, tipo_novedad, fecha_inicio, fecha_fin, float(valor)
            ))
            conn.commit()
            if request.is_json:
                return jsonify({'success': True, 'message': 'Novedad actualizada correctamente'})
            flash('Novedad actualizada correctamente', 'success')
            return redirect(url_for('novedades.listar_novedades'))
        except Exception as e:
            conn.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': f'Error al actualizar: {e}'}), 500
            flash(f'Error al actualizar: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
        # Si es JSON y no se retornó antes, error genérico
        if request.is_json:
            return jsonify({'success': False, 'message': 'Error desconocido al actualizar novedad'}), 500

    # GET: obtener novedad y devolver JSON si es petición Angular
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"Buscando novedad con ID: {novedad_id}")
        cursor.execute('EXEC Novedad.sp_obtener_novedad_por_id ?', (novedad_id,))
        novedad = cursor.fetchone()
        print(f"Resultado novedad: {novedad} (type: {type(novedad)})")
        print(f"cursor.description: {cursor.description}")
        columnas = [col[0] for col in cursor.description] if cursor.description else []
        print(f"Columnas detectadas: {columnas}")
        novedad_dict = dict(zip(columnas, novedad)) if novedad else None
        print(f"JSON enviado a Angular: {novedad_dict}")
    except Exception as e:
        if request.accept_mimetypes['application/json'] or request.is_json:
            return jsonify({'error': f'Error al obtener novedad: {e}'}), 500
        flash(f'Error al obtener novedad: {e}', 'error')
        novedad = None
    finally:
        cursor.close()
        conn.close()

    if not novedad:
        if request.accept_mimetypes['application/json'] or request.is_json:
            return jsonify({'error': 'Novedad no encontrada'}), 404
        flash("Novedad no encontrada", "error")
        return redirect(url_for('novedades.listar_novedades'))

    # Si la petición es JSON (Angular), devolver los datos en JSON
    if request.accept_mimetypes['application/json'] or request.is_json:
        return jsonify(novedad_dict)

    # Si no, renderizar la plantilla legacy
    return render_template('novedades_editar.html', novedad=novedad)
