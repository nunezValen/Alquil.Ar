# 📋 Cancelación Automática de Alquileres Futuros - Alquileres Adeudados

## 🎯 **Funcionalidad Implementada**

Cuando un alquiler en estado **"en_curso"** vence (no es devuelto en su fecha de finalización), el sistema automáticamente:

1. ✅ **Cambia el estado** del alquiler a **"adeudado"**
2. ✅ **Marca la unidad** como **"adeudada"** 
3. ✅ **Busca todos los alquileres futuros** de la misma unidad
4. ✅ **Cancela automáticamente** todos los alquileres futuros
5. ✅ **Envía emails de cancelación** a todos los clientes afectados
6. ✅ **Procesa los reembolsos** según la política establecida

---

## 🔄 **Cuándo se Ejecuta**

### **Automáticamente:**
- Cada vez que un empleado accede a **"Gestión" → "Lista de Alquileres"**
- Se ejecuta la función `procesar_alquileres_vencidos_automatico()`

### **Manualmente:**
- Ejecutando el comando: `python manage.py procesar_alquileres_vencidos`
- Con modo verbose: `python manage.py procesar_alquileres_vencidos --verbose`
- Con modo dry-run: `python manage.py procesar_alquileres_vencidos --dry-run --verbose`

---

## 🛠️ **Funcionamiento Técnico**

### **Código Modificado:**

#### **1. Función Principal (`persona/views.py`)**
```python
def procesar_alquileres_vencidos_automatico():
    # Buscar alquileres vencidos
    alquileres_vencidos = Alquiler.objects.filter(
        estado='en_curso',
        fecha_fin__lt=date.today()
    )
    
    for alquiler in alquileres_vencidos:
        # Cambiar a adeudado
        alquiler.estado = 'adeudado'
        alquiler.save()
        
        # Marcar unidad como adeudada
        alquiler.unidad.estado = 'adeudado'
        alquiler.unidad.save()
        
        # NUEVA FUNCIONALIDAD: Cancelar alquileres futuros
        alquileres_futuros = Alquiler.objects.filter(
            unidad=alquiler.unidad,
            estado__in=['reservado', 'en_curso'],
            fecha_inicio__gt=date.today()
        ).exclude(id=alquiler.id)
        
        for alquiler_futuro in alquileres_futuros:
            # Cancelar con reembolso
            alquiler_futuro.cancelar(empleado=usuario_sistema)
            
            # Enviar email de cancelación
            enviar_email_alquiler_cancelado(alquiler_futuro)
```

#### **2. Comando de Gestión (`maquinas/management/commands/procesar_alquileres_vencidos.py`)**
- Misma lógica aplicada
- Incluye modo `--verbose` para ver detalles
- Incluye modo `--dry-run` para simular sin cambios

---

## 📧 **Comunicación con Clientes**

### **Email de Cancelación Automática:**
```
Asunto: Cancelación de Alquiler - ALQUIL.AR

Estimado [Cliente],

Lamentamos informarte que tu alquiler [NÚMERO] ha sido cancelado automáticamente.

Motivo: Cancelado automáticamente por alquiler adeudado #A-0001. 
La máquina [PATENTE] no fue devuelto a tiempo.

Reembolso: [PORCENTAJE]% del monto total ($ [MONTO])

El reembolso se procesará según nuestras políticas establecidas.

Disculpas por las molestias ocasionadas.

Saludos,
Equipo ALQUIL.AR
```

---

## 💰 **Política de Reembolsos**

Los alquileres futuros cancelados automáticamente reciben **reembolso del 100%** porque:

1. **No es culpa del cliente** → La cancelación es por un problema de otra persona
2. **Cancelación por empleado** → Se considera cancelación administrativa
3. **Política de buena fe** → Mantener la reputación del servicio

---

## 🧪 **Cómo Probar la Funcionalidad**

### **Opción 1: Script de Prueba Automática**
```bash
python probar_cancelacion_automatica.py
```

### **Opción 2: Prueba Manual**
1. **Crear un alquiler vencido:**
   ```bash
   python crear_alquiler_vencido_real.py
   ```

2. **Crear alquileres futuros** de la misma unidad

3. **Acceder a la gestión:**
   - Ir a **"Gestión" → "Lista de Alquileres"**
   - El procesamiento automático se ejecutará

4. **Verificar resultados:**
   - Alquiler vencido → Estado "adeudado"
   - Unidad → Estado "adeudado"
   - Alquileres futuros → Estado "cancelado"
   - Emails enviados a clientes

---

## 📊 **Logs del Sistema**

### **Logs de Éxito:**
```
[ADEUDADO] Se cancelaron 3 alquileres futuros por alquiler adeudado A-0001
  - A-0002: Juan Pérez - Reembolso: 100% ($15000)
  - A-0003: María García - Reembolso: 100% ($18000)
  - A-0004: Carlos López - Reembolso: 100% ($12000)
[ADEUDADO] Email de cancelación enviado para alquiler A-0002
[ADEUDADO] Email de cancelación enviado para alquiler A-0003
[ADEUDADO] Email de cancelación enviado para alquiler A-0004
```

### **Logs de Error:**
```
[ADEUDADO] Error cancelando alquiler futuro A-0002: [Error específico]
[ADEUDADO] Error al enviar email de cancelación para alquiler A-0003: [Error específico]
```

---

## 🔍 **Casos de Uso**

### **Caso 1: Cliente No Devuelve Máquina**
1. **Alquiler A-0001** (Juan) está "en_curso" hasta 15/07/2025
2. **Fecha actual:** 16/07/2025 → Alquiler vencido
3. **Alquileres futuros de la misma unidad:**
   - A-0002 (María): 20/07/2025 - 22/07/2025 
   - A-0003 (Carlos): 25/07/2025 - 27/07/2025

**Resultado:**
- ✅ A-0001 → "adeudado"
- ✅ A-0002 → "cancelado" (100% reembolso)
- ✅ A-0003 → "cancelado" (100% reembolso)
- ✅ Emails enviados a María y Carlos

### **Caso 2: Sin Alquileres Futuros**
1. **Alquiler A-0001** vence
2. **No hay alquileres futuros** de la misma unidad

**Resultado:**
- ✅ A-0001 → "adeudado"
- ✅ Unidad → "adeudada"
- ✅ No hay cancelaciones adicionales

---

## ⚠️ **Consideraciones Importantes**

### **Seguridad:**
- ✅ Solo se cancelan alquileres **futuros** (fecha_inicio > hoy)
- ✅ No se cancelan alquileres **en_curso** 
- ✅ No se cancelan alquileres ya **finalizados**

### **Performance:**
- ✅ Procesamiento en lotes
- ✅ Manejo de errores sin interrumpir el flujo
- ✅ Logs detallados para debugging

### **Comunicación:**
- ✅ Emails automáticos a clientes afectados
- ✅ Información clara sobre motivo de cancelación
- ✅ Detalles de reembolso incluidos

---

## 🎯 **Beneficios del Sistema**

1. **Automatización Completa** → No requiere intervención manual
2. **Protección al Cliente** → Reembolsos automáticos del 100%
3. **Comunicación Transparente** → Emails inmediatos con explicaciones
4. **Gestión Eficiente** → Libera unidades bloqueadas automáticamente
5. **Trazabilidad** → Logs detallados de todas las acciones
6. **Flexibilidad** → Modo dry-run para testing

---

## 🚀 **Estados del Sistema**

### **Flujo Normal:**
```
reservado → en_curso → finalizado
```

### **Flujo con Problema:**
```
reservado → en_curso → adeudado
                         ↓
               [Cancelación automática 
                de alquileres futuros]
```

---

## 📞 **Soporte y Mantenimiento**

Para cualquier problema con la funcionalidad:

1. **Verificar logs** del sistema
2. **Ejecutar modo dry-run** para ver qué se procesaría
3. **Revisar emails** enviados a clientes
4. **Validar reembolsos** procesados
5. **Contactar soporte técnico** si es necesario

La funcionalidad está **completamente implementada y probada** ✅ 