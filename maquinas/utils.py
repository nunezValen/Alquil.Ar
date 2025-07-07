import io
from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader


def generar_pdf_factura_alquiler(alquiler):
    """
    Genera un PDF con formato de factura para el alquiler
    """
    buffer = io.BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Obtener estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2e7d32'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.HexColor('#1976d2'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.HexColor('#424242'),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#424242')
    )
    
    # Lista para almacenar los elementos del PDF
    elements = []
    
    # Encabezado de la empresa
    elements.append(Paragraph("ALQUIL.AR", title_style))
    elements.append(Paragraph("Sistema de Alquiler de Maquinaria", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Información de la empresa
    empresa_info = [
        ["<b>ALQUIL.AR S.A.</b>", ""],
        ["CUIT: 30-12345678-9", ""],
        ["Av. Corrientes 1234, Buenos Aires", ""],
        ["Tel: +54 11 1234-5678", ""],
        ["Email: info@alquil.ar", ""],
    ]
    
    empresa_table = Table(empresa_info, colWidths=[8*cm, 8*cm])
    empresa_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(empresa_table)
    elements.append(Spacer(1, 30))
    
    # Información del comprobante
    fecha_actual = datetime.now()
    comprobante_info = [
        ["<b>COMPROBANTE DE ALQUILER</b>", f"<b>Nº {alquiler.numero}</b>"],
        [f"Fecha de emisión: {fecha_actual.strftime('%d/%m/%Y')}", f"Hora: {fecha_actual.strftime('%H:%M')}"],
        ["Tipo: Alquiler de Maquinaria", f"Estado: {alquiler.get_estado_display()}"],
    ]
    
    comprobante_table = Table(comprobante_info, colWidths=[10*cm, 6*cm])
    comprobante_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e8')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(comprobante_table)
    elements.append(Spacer(1, 30))
    
    # Información del cliente
    elements.append(Paragraph("<b>DATOS DEL CLIENTE</b>", header_style))
    
    cliente_info = [
        ["Nombre completo:", f"{alquiler.persona.nombre} {alquiler.persona.apellido}"],
        ["DNI:", alquiler.persona.dni],
        ["Email:", alquiler.persona.email],
        ["Teléfono:", alquiler.persona.telefono],
        ["Dirección:", alquiler.persona.direccion],
    ]
    
    cliente_table = Table(cliente_info, colWidths=[4*cm, 12*cm])
    cliente_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(cliente_table)
    elements.append(Spacer(1, 30))
    
    # Información de la máquina y el alquiler
    elements.append(Paragraph("<b>DETALLE DEL ALQUILER</b>", header_style))
    
    maquina_info = [
        ["Máquina:", alquiler.maquina_base.nombre],
        ["Marca:", alquiler.maquina_base.get_marca_display()],
        ["Modelo:", alquiler.maquina_base.modelo],
        ["Tipo:", alquiler.maquina_base.get_tipo_display()],
    ]
    
    if alquiler.unidad:
        maquina_info.extend([
            ["Unidad Asignada:", f"Patente {alquiler.unidad.patente}"],
            ["Sucursal de Retiro:", alquiler.unidad.sucursal.direccion],
        ])
    
    maquina_info.extend([
        ["Fecha de Inicio:", alquiler.fecha_inicio.strftime('%d/%m/%Y')],
        ["Fecha de Fin:", alquiler.fecha_fin.strftime('%d/%m/%Y')],
        ["Duración:", f"{alquiler.cantidad_dias} día{'s' if alquiler.cantidad_dias != 1 else ''}"],
        ["Método de Pago:", alquiler.get_metodo_pago_display()],
    ])
    
    maquina_table = Table(maquina_info, colWidths=[4*cm, 12*cm])
    maquina_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(maquina_table)
    elements.append(Spacer(1, 30))
    
    # Código de retiro destacado
    if alquiler.codigo_retiro:
        elements.append(Paragraph("<b>CÓDIGO DE RETIRO</b>", header_style))
        
        codigo_info = [
            [f"<font size=16><b>{alquiler.codigo_retiro}</b></font>"],
        ]
        
        codigo_table = Table(codigo_info, colWidths=[16*cm])
        codigo_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#fff3cd')),
            ('BOX', (0, 0), (0, 0), 2, colors.HexColor('#ffc107')),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (0, 0), 15),
            ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ]))
        
        elements.append(codigo_table)
        elements.append(Paragraph("<i>Presenta este código en la sucursal para retirar la máquina</i>", 
                                ParagraphStyle('ItalicStyle', parent=normal_style, alignment=TA_CENTER, fontSize=9)))
        elements.append(Spacer(1, 20))
    
    # Resumen financiero
    elements.append(Paragraph("<b>RESUMEN FINANCIERO</b>", header_style))
    
    precio_unitario = alquiler.monto_total / alquiler.cantidad_dias
    
    resumen_info = [
        ["Concepto", "Cantidad", "Precio Unitario", "Subtotal"],
        [f"Alquiler {alquiler.maquina_base.nombre}", 
         f"{alquiler.cantidad_dias} día{'s' if alquiler.cantidad_dias != 1 else ''}", 
         f"${precio_unitario:.2f}", 
         f"${alquiler.monto_total:.2f}"],
        ["", "", "<b>TOTAL A PAGAR:</b>", f"<b>${alquiler.monto_total:.2f}</b>"],
    ]
    
    resumen_table = Table(resumen_info, colWidths=[8*cm, 3*cm, 3*cm, 2*cm])
    resumen_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, 1), 'LEFT'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#e8f5e8')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(resumen_table)
    elements.append(Spacer(1, 40))
    
    # Términos y condiciones
    elements.append(Paragraph("<b>TÉRMINOS Y CONDICIONES</b>", header_style))
    
    terminos = [
        "• El cliente debe presentar el código de retiro y documento de identidad para retirar la máquina.",
        "• La máquina debe ser devuelta en el mismo estado en que se entregó.",
        "• El horario de retiro y devolución es de Lunes a Viernes de 8:00 a 17:00 hs.",
        "• Cualquier daño o pérdida será cobrado según tarifa vigente.",
        "• El alquiler incluye seguro básico contra terceros.",
        "• Para cancelaciones, consultar política en nuestro sitio web.",
    ]
    
    for termino in terminos:
        elements.append(Paragraph(termino, normal_style))
    
    elements.append(Spacer(1, 30))
    
    # Pie de página
    pie_info = [
        ["<b>ALQUIL.AR</b> - Su socio confiable en alquiler de maquinaria"],
        ["Web: www.alquil.ar | Email: info@alquil.ar | Tel: +54 11 1234-5678"],
        [f"Comprobante generado el {fecha_actual.strftime('%d/%m/%Y a las %H:%M')}"],
    ]
    
    pie_table = Table(pie_info, colWidths=[16*cm])
    pie_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 10),
        ('FONTSIZE', (0, 1), (0, 2), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(pie_table)
    
    # Construir el PDF
    doc.build(elements)
    
    # Obtener el contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def enviar_email_alquiler_simple(alquiler):
    """
    Envía un email simple de confirmación de alquiler (sin PDF)
    """
    try:
        print(f"[INFO] Iniciando envío de email para alquiler {alquiler.numero}")
        print(f"[INFO] Email destino: {alquiler.persona.email}")
        
        # Crear el mensaje de email
        asunto = f'Confirmación de Alquiler #{alquiler.numero} - ALQUIL.AR'
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; background: linear-gradient(135deg, #2e7d32, #4caf50); padding: 30px; border-radius: 10px; color: white; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 28px;">¡Alquiler Confirmado!</h1>
                    <p style="margin: 10px 0 0; font-size: 16px;">Gracias por confiar en ALQUIL.AR</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #2e7d32; margin-top: 0;">Detalles de tu Alquiler</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Número de Alquiler:</td>
                            <td style="padding: 8px 0; color: #2e7d32; font-weight: bold;">{alquiler.numero}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Código de Retiro:</td>
                            <td style="padding: 8px 0; color: #ff6f00; font-weight: bold; font-size: 18px;">{alquiler.codigo_retiro}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Máquina:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.nombre}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Marca y Modelo:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.get_marca_display()} {alquiler.maquina_base.modelo}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Período:</td>
                            <td style="padding: 8px 0;">{alquiler.fecha_inicio.strftime('%d/%m/%Y')} - {alquiler.fecha_fin.strftime('%d/%m/%Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Duración:</td>
                            <td style="padding: 8px 0;">{alquiler.cantidad_dias} día{'s' if alquiler.cantidad_dias != 1 else ''}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Monto Total:</td>
                            <td style="padding: 8px 0; color: #2e7d32; font-weight: bold; font-size: 16px;">${float(alquiler.monto_total) if alquiler.monto_total else 0:.2f}</td>
                        </tr>
        """
        
        if alquiler.unidad and alquiler.unidad.sucursal:
            mensaje_html += f"""
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Sucursal de Retiro:</td>
                            <td style="padding: 8px 0;">{alquiler.unidad.sucursal.direccion}</td>
                        </tr>
            """
        
        mensaje_html += f"""
                    </table>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #856404; margin-top: 0; text-align: center;">📋 Instrucciones para el Retiro</h3>
                    <ul style="color: #856404; margin: 0;">
                        <li><strong>Presenta tu código de retiro:</strong> {alquiler.codigo_retiro}</li>
                        <li><strong>Lleva tu documento de identidad</strong></li>
                        <li><strong>Horario:</strong> Lunes a Viernes de 8:00 a 17:00 hs</li>
                        <li><strong>Revisa el estado</strong> de la máquina antes de retirarla</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin: 0;">¿Tienes alguna consulta?</p>
                    <p style="margin: 5px 0;">
                        📧 <a href="mailto:contacto.alquilar@gmail.com" style="color: #2e7d32;">contacto.alquilar@gmail.com</a> | 
                        📞 <a href="tel:+541112345678" style="color: #2e7d32;">+54 11 1234-5678</a>
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; background: #f1f3f4; border-radius: 10px; margin-top: 30px;">
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        <strong>ALQUIL.AR</strong> - Tu socio confiable en alquiler de maquinaria<br>
                        Este es un email automático, por favor no respondas a esta dirección.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear el email
        from django.core.mail import send_mail
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        
        # Enviar el email
        print("[INFO] Enviando email...")
        print(f"[INFO] From: {from_email}")
        print(f"[INFO] To: {alquiler.persona.email}")
        print(f"[INFO] Subject: {asunto}")
        
        send_mail(
            subject=asunto,
            message='',  # Mensaje en texto plano vacío
            from_email=from_email,
            recipient_list=[alquiler.persona.email],
            html_message=mensaje_html,  # Mensaje HTML
            fail_silently=False
        )
        
        print(f"[SUCCESS] Email enviado exitosamente a: {alquiler.persona.email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al enviar email: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback completo:")
        traceback.print_exc()
        return False


def enviar_email_alquiler_cancelado(alquiler):
    """
    Envía un email de notificación de cancelación de alquiler
    """
    try:
        print(f"[INFO] Iniciando envío de email de cancelación para alquiler {alquiler.numero}")
        print(f"[INFO] Email destino: {alquiler.persona.email}")
        
        # Determinar quién canceló
        if alquiler.cancelado_por_empleado:
            cancelado_por = "nuestro equipo"
            motivo_section = f"""
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #856404; margin-top: 0; text-align: center;">ℹ️ Motivo de la Cancelación</h3>
                    <p style="color: #856404; margin: 0; text-align: center;">
                        {alquiler.observaciones_cancelacion if alquiler.observaciones_cancelacion else 'La cancelación fue procesada por nuestro equipo administrativo.'}
                    </p>
                </div>
            """
        else:
            cancelado_por = "usted"
            motivo_section = ""
        
        # Información de reembolso
        if alquiler.monto_reembolso and alquiler.monto_reembolso > 0:
            reembolso_section = f"""
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #155724; margin-top: 0; text-align: center;">💰 Información de Reembolso</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #155724;">Porcentaje de Reembolso:</td>
                            <td style="padding: 8px 0; color: #155724; font-weight: bold;">{alquiler.porcentaje_reembolso}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #155724;">Monto a Reembolsar:</td>
                            <td style="padding: 8px 0; color: #155724; font-weight: bold; font-size: 16px;">${float(alquiler.monto_reembolso):.2f}</td>
                        </tr>
                    </table>
                    <p style="color: #155724; margin: 10px 0 0; font-size: 14px; text-align: center;">
                        <strong>El reembolso será procesado en los próximos días hábiles.</strong><br>
                        Acércate a la sucursal {alquiler.unidad.sucursal.direccion} con tu documento para cobrarlo.
                    </p>
                </div>
            """
        else:
            reembolso_section = f"""
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #721c24; margin-top: 0; text-align: center;">⚠️ Sin Reembolso</h3>
                    <p style="color: #721c24; margin: 0; text-align: center;">
                        Según nuestra política de cancelación, no corresponde reembolso para este alquiler.
                    </p>
                </div>
            """
        
        # Crear el mensaje de email
        asunto = f'Cancelación de Alquiler #{alquiler.numero} - ALQUIL.AR'
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; background: linear-gradient(135deg, #dc3545, #c82333); padding: 30px; border-radius: 10px; color: white; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 28px;">Alquiler Cancelado</h1>
                    <p style="margin: 10px 0 0; font-size: 16px;">Su alquiler ha sido cancelado</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #dc3545; margin-top: 0;">Detalles del Alquiler</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Número de Alquiler:</td>
                            <td style="padding: 8px 0; color: #dc3545; font-weight: bold;">{alquiler.numero}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Máquina:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.nombre}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Marca y Modelo:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.get_marca_display()} {alquiler.maquina_base.modelo}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Período Original:</td>
                            <td style="padding: 8px 0;">{alquiler.fecha_inicio.strftime('%d/%m/%Y')} - {alquiler.fecha_fin.strftime('%d/%m/%Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Duración:</td>
                            <td style="padding: 8px 0;">{alquiler.cantidad_dias} día{'s' if alquiler.cantidad_dias != 1 else ''}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Monto Original:</td>
                            <td style="padding: 8px 0; color: #555; font-weight: bold; font-size: 16px;">${float(alquiler.monto_total) if alquiler.monto_total else 0:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Cancelado por:</td>
                            <td style="padding: 8px 0; color: #dc3545; font-weight: bold;">{cancelado_por.title()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Fecha de Cancelación:</td>
                            <td style="padding: 8px 0;">{alquiler.fecha_cancelacion.strftime('%d/%m/%Y a las %H:%M') if alquiler.fecha_cancelacion else 'No disponible'}</td>
                        </tr>
                    </table>
                </div>
                
                {motivo_section}
                {reembolso_section}
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin: 0;">¿Tienes alguna consulta sobre la cancelación?</p>
                    <p style="margin: 5px 0;">
                        📧 <a href="mailto:contacto.alquilar@gmail.com" style="color: #dc3545;">contacto.alquilar@gmail.com</a> | 
                        📞 <a href="tel:+541112345678" style="color: #dc3545;">+54 11 1234-5678</a>
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; background: #f1f3f4; border-radius: 10px; margin-top: 30px;">
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        <strong>ALQUIL.AR</strong> - Tu socio confiable en alquiler de maquinaria<br>
                        Lamentamos los inconvenientes. Esperamos volver a servirte pronto.<br>
                        Este es un email automático, por favor no respondas a esta dirección.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear el email
        from django.core.mail import send_mail
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        
        # Enviar el email
        print("[INFO] Enviando email de cancelación...")
        print(f"[INFO] From: {from_email}")
        print(f"[INFO] To: {alquiler.persona.email}")
        print(f"[INFO] Subject: {asunto}")
        
        send_mail(
            subject=asunto,
            message='',  # Mensaje en texto plano vacío
            from_email=from_email,
            recipient_list=[alquiler.persona.email],
            html_message=mensaje_html,  # Mensaje HTML
            fail_silently=False
        )
        
        print(f"[SUCCESS] Email de cancelación enviado exitosamente a: {alquiler.persona.email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al enviar email de cancelación: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback completo:")
        traceback.print_exc()
        return False 


def enviar_email_inicio_alquiler(alquiler):
    """
    Envía un email de notificación de inicio de alquiler
    """
    try:
        print(f"[INFO] Iniciando envío de email de inicio para alquiler {alquiler.numero}")
        print(f"[INFO] Email destino: {alquiler.persona.email}")
        
        # Crear el mensaje de email
        asunto = f'Alquiler Iniciado #{alquiler.numero} - ALQUIL.AR'
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; background: linear-gradient(135deg, #28a745, #20c997); padding: 30px; border-radius: 10px; color: white; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 28px;">🚀 ¡Alquiler Iniciado!</h1>
                    <p style="margin: 10px 0 0; font-size: 16px;">Su alquiler ha comenzado oficialmente</p>
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #155724; margin-top: 0; text-align: center;">✅ Estado: EN CURSO</h2>
                    <p style="color: #155724; margin: 0; text-align: center; font-size: 16px;">
                        Su alquiler está ahora activo y puede comenzar a utilizar la máquina.
                    </p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #28a745; margin-top: 0;">Detalles del Alquiler</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Número de Alquiler:</td>
                            <td style="padding: 8px 0; color: #28a745; font-weight: bold;">{alquiler.numero}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Máquina:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.nombre}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Marca y Modelo:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.get_marca_display()} {alquiler.maquina_base.modelo}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Período de Alquiler:</td>
                            <td style="padding: 8px 0;">{alquiler.fecha_inicio.strftime('%d/%m/%Y')} - {alquiler.fecha_fin.strftime('%d/%m/%Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Duración:</td>
                            <td style="padding: 8px 0;">{alquiler.cantidad_dias} día{'s' if alquiler.cantidad_dias != 1 else ''}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Código de Retiro:</td>
                            <td style="padding: 8px 0; color: #28a745; font-weight: bold; font-size: 16px;">{alquiler.codigo_retiro}</td>
                        </tr>
                    </table>
                </div>
                
                {f'''
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #856404; margin-top: 0; text-align: center;">📍 Información de la Unidad</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #856404;">Patente:</td>
                            <td style="padding: 8px 0; color: #856404; font-weight: bold;">{alquiler.unidad.patente}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #856404;">Sucursal:</td>
                            <td style="padding: 8px 0; color: #856404;">{alquiler.unidad.sucursal.direccion}</td>
                        </tr>
                    </table>
                </div>
                ''' if alquiler.unidad else ''}
                
                <div style="background: #e7f3ff; border: 1px solid #b3d9ff; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #0066cc; margin-top: 0; text-align: center;">📋 Instrucciones Importantes</h3>
                    <ul style="color: #0066cc; margin: 0; padding-left: 20px;">
                        <li>Su alquiler está ahora activo y puede utilizar la máquina</li>
                        <li>Conserve este email como comprobante del inicio del alquiler</li>
                        <li>Recuerde devolver la máquina en la fecha acordada: <strong>{alquiler.fecha_fin.strftime('%d/%m/%Y')}</strong></li>
                        <li>En caso de problemas o consultas, contacte inmediatamente a nuestro equipo</li>
                        <li>Utilice la máquina de forma responsable y siguiendo las instrucciones de seguridad</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin: 0;">¿Tienes alguna consulta sobre tu alquiler?</p>
                    <p style="margin: 5px 0;">
                        📧 <a href="mailto:contacto.alquilar@gmail.com" style="color: #28a745;">contacto.alquilar@gmail.com</a> | 
                        📞 <a href="tel:+541112345678" style="color: #28a745;">+54 11 1234-5678</a>
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; background: #f1f3f4; border-radius: 10px; margin-top: 30px;">
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        <strong>ALQUIL.AR</strong> - Tu socio confiable en alquiler de maquinaria<br>
                        ¡Que tengas un excelente alquiler!<br>
                        Este es un email automático, por favor no respondas a esta dirección.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear el email
        from django.core.mail import send_mail
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        
        # Enviar el email
        print("[INFO] Enviando email de inicio...")
        print(f"[INFO] From: {from_email}")
        print(f"[INFO] To: {alquiler.persona.email}")
        print(f"[INFO] Subject: {asunto}")
        
        send_mail(
            subject=asunto,
            message='',  # Mensaje en texto plano vacío
            from_email=from_email,
            recipient_list=[alquiler.persona.email],
            html_message=mensaje_html,  # Mensaje HTML
            fail_silently=False
        )
        
        print(f"[SUCCESS] Email de inicio enviado exitosamente a: {alquiler.persona.email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al enviar email de inicio: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback completo:")
        traceback.print_exc()
        return False


def enviar_email_finalizacion_alquiler(alquiler):
    """
    Envía un email de notificación de finalización de alquiler
    """
    try:
        print(f"[INFO] Iniciando envío de email de finalización para alquiler {alquiler.numero}")
        print(f"[INFO] Email destino: {alquiler.persona.email}")
        
        # Obtener la calificación si existe
        calificacion_info = ""
        try:
            from .models import CalificacionCliente
            calificacion = CalificacionCliente.objects.get(alquiler=alquiler)
            estrellas = "⭐" * calificacion.calificacion
            calificacion_info = f"""
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                <h3 style="color: #856404; margin-top: 0; text-align: center;">⭐ Calificación Recibida</h3>
                <p style="text-align: center; color: #856404; font-size: 18px; margin: 10px 0;">
                    {estrellas} ({calificacion.calificacion}/5)
                </p>
                {f'<p style="text-align: center; color: #856404; margin: 0;"><em>"{calificacion.observaciones}"</em></p>' if calificacion.observaciones else ''}
            </div>
            """
        except:
            pass
        
        # Crear el mensaje de email
        asunto = f'Alquiler Finalizado #{alquiler.numero} - ALQUIL.AR'
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; background: linear-gradient(135deg, #17a2b8, #138496); padding: 30px; border-radius: 10px; color: white; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 28px;">🏁 ¡Alquiler Finalizado!</h1>
                    <p style="margin: 10px 0 0; font-size: 16px;">Su alquiler ha sido completado exitosamente</p>
                </div>
                
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #0c5460; margin-top: 0; text-align: center;">✅ Estado: FINALIZADO</h2>
                    <p style="color: #0c5460; margin: 0; text-align: center; font-size: 16px;">
                        Su alquiler ha sido completado y la máquina ha sido devuelta correctamente.
                    </p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #17a2b8; margin-top: 0;">Resumen del Alquiler</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Número de Alquiler:</td>
                            <td style="padding: 8px 0; color: #17a2b8; font-weight: bold;">{alquiler.numero}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Máquina:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.nombre}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Marca y Modelo:</td>
                            <td style="padding: 8px 0;">{alquiler.maquina_base.get_marca_display()} {alquiler.maquina_base.modelo}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Período de Alquiler:</td>
                            <td style="padding: 8px 0;">{alquiler.fecha_inicio.strftime('%d/%m/%Y')} - {alquiler.fecha_fin.strftime('%d/%m/%Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Duración:</td>
                            <td style="padding: 8px 0;">{alquiler.cantidad_dias} día{'s' if alquiler.cantidad_dias != 1 else ''}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Monto Total:</td>
                            <td style="padding: 8px 0; color: #17a2b8; font-weight: bold; font-size: 16px;">${float(alquiler.monto_total) if alquiler.monto_total else 0:.2f}</td>
                        </tr>
                    </table>
                </div>
                
                {calificacion_info}
                
                <div style="background: #e7f3ff; border: 1px solid #b3d9ff; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #0066cc; margin-top: 0; text-align: center;">🎉 ¡Gracias por elegirnos!</h3>
                    <p style="color: #0066cc; text-align: center; margin: 10px 0;">
                        Esperamos que haya tenido una excelente experiencia con nuestro servicio.
                    </p>
                    <p style="color: #0066cc; text-align: center; margin: 10px 0;">
                        Su opinión es muy importante para nosotros y nos ayuda a mejorar continuamente.
                    </p>
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #155724; margin-top: 0; text-align: center;">🔄 ¿Necesita alquilar otra máquina?</h3>
                    <p style="color: #155724; text-align: center; margin: 10px 0;">
                        Visite nuestro catálogo en línea para ver todas las máquinas disponibles.
                    </p>
                    <p style="color: #155724; text-align: center; margin: 10px 0;">
                        Como cliente recurrente, puede acceder a ofertas especiales y descuentos.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin: 0;">¿Tienes alguna consulta o comentario?</p>
                    <p style="margin: 5px 0;">
                        📧 <a href="mailto:contacto.alquilar@gmail.com" style="color: #17a2b8;">contacto.alquilar@gmail.com</a> | 
                        📞 <a href="tel:+541112345678" style="color: #17a2b8;">+54 11 1234-5678</a>
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; background: #f1f3f4; border-radius: 10px; margin-top: 30px;">
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        <strong>ALQUIL.AR</strong> - Tu socio confiable en alquiler de maquinaria<br>
                        ¡Gracias por confiar en nosotros!<br>
                        Este es un email automático, por favor no respondas a esta dirección.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear el email
        from django.core.mail import send_mail
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        
        # Enviar el email
        print("[INFO] Enviando email de finalización...")
        print(f"[INFO] From: {from_email}")
        print(f"[INFO] To: {alquiler.persona.email}")
        print(f"[INFO] Subject: {asunto}")
        
        send_mail(
            subject=asunto,
            message='',  # Mensaje en texto plano vacío
            from_email=from_email,
            recipient_list=[alquiler.persona.email],
            html_message=mensaje_html,  # Mensaje HTML
            fail_silently=False
        )
        
        print(f"[SUCCESS] Email de finalización enviado exitosamente a: {alquiler.persona.email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al enviar email de finalización: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback completo:")
        traceback.print_exc()
        return False