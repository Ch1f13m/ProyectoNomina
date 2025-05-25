from flask import Blueprint, jsonify, request, send_file
from bson import ObjectId
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
from config import mongo_db  # Asegúrate de tener esto bien definido

bp = Blueprint('nomina_report_mongo', __name__, url_prefix='/api/reportes')


@bp.route('/historial/<int:contrato_id>', methods=['GET'])
def historial_nominas(contrato_id):
    historial = list(mongo_db.reportes_nomina.find({"contrato_id": contrato_id}))
    for h in historial:
        h['_id'] = str(h['_id'])
    return jsonify(historial)


@bp.route('/generar-pdf/<string:reporte_id>', methods=['GET'])
def generar_pdf(reporte_id):
    reporte = mongo_db.reportes_nomina.find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return jsonify({"error": "Reporte no encontrado"}), 404

    buffer = BytesIO()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, f"Resumen de Nómina - Contrato {reporte['contrato_id']}", ln=1, align='C')
    pdf.cell(200, 10, f"Periodo: {reporte['periodo']} - Fecha: {reporte.get('fecha', datetime.now()).strftime('%Y-%m-%d')}", ln=1)

    # Datos básicos
    pdf.ln(5)
    pdf.cell(200, 10, f"Salario: ${reporte['salario']:,.2f}", ln=1)
    pdf.cell(200, 10, f"Auxilio Transporte: ${reporte['auxilio']:,.2f}", ln=1)
    pdf.cell(200, 10, f"Otros Ingresos: ${reporte['otros_ingresos']:,.2f}", ln=1)
    pdf.cell(200, 10, f"Deducciones: ${reporte['deducciones']:,.2f}", ln=1)

    def tabla(nombre, lista):
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, nombre, ln=1)
        pdf.set_font("Arial", size=10)
        for item in lista:
            pdf.cell(200, 8, f"{item['tipo']}: ${item['valor']:,.2f}", ln=1)

    tabla("Prestaciones Sociales", reporte.get("prestaciones", []))
    tabla("Aportes Seguridad Social", reporte.get("aportes", []))
    tabla("Parafiscales", reporte.get("parafiscales", []))

    if "retencion" in reporte:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Retención en la Fuente", ln=1)
        pdf.set_font("Arial", size=10)
        r = reporte['retencion']
        pdf.cell(200, 8, f"Base: ${r['base']:,.2f} | Porcentaje: {r['porcentaje']}% | Valor: ${r['valor']:,.2f}", ln=1)

    pdf.output(buffer)
    buffer.seek(0)

    return send_file(buffer, download_name=f"reporte_nomina_{reporte['contrato_id']}.pdf", as_attachment=True)
