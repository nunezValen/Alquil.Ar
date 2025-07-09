// Script para validar unicidad de nombre de máquina base en tiempo real y validar campos requeridos y reglas específicas

document.addEventListener('DOMContentLoaded', function() {
    // Detectar si estamos en edición y obtener el nombre original
    const nombreInput = document.querySelector('input[name="nombre"]');
    if (!nombreInput) return;
    const form = nombreInput.closest('form');
    const submitBtn = form.querySelector('button[type="submit"]');
    let nombreOriginal = nombreInput.getAttribute('data-nombre-original') || '';

    // Crear o reutilizar el div de error para nombre
    let errorDiv = document.createElement('div');
    errorDiv.className = 'error-text';
    errorDiv.style.display = 'none';
    nombreInput.parentNode.appendChild(errorDiv);

    let nombresExistentes = [];

    // Cargar los nombres existentes una sola vez
    fetch('/maquinas/nombres_maquinas_base/')
        .then(response => response.json())
        .then(data => {
            nombresExistentes = (data.nombres || []).map(n => n.toLowerCase().trim());
        });

    function validarNombre() {
        const valor = nombreInput.value.trim().toLowerCase();
        // Permitir el nombre original en edición
        if (nombreOriginal && valor === nombreOriginal.trim().toLowerCase()) {
            errorDiv.style.display = 'none';
            nombreInput.classList.remove('is-invalid');
            return true;
        }
        if (valor && nombresExistentes.includes(valor)) {
            errorDiv.textContent = 'Ya existe una máquina con ese nombre.';
            errorDiv.style.display = 'block';
            nombreInput.classList.add('is-invalid');
            return false;
        } else if (!valor) {
            errorDiv.textContent = 'El nombre es obligatorio.';
            errorDiv.style.display = 'block';
            nombreInput.classList.add('is-invalid');
            return false;
        } else {
            errorDiv.style.display = 'none';
            nombreInput.classList.remove('is-invalid');
            return true;
        }
    }

    function contieneDecimal(valor) {
        return /[.,]/.test(valor);
    }

    function mostrarErrorUnico(campo, mensaje) {
        campo.classList.add('is-invalid');
        // Elimina todos los errores previos de este campo
        let errores = campo.parentNode.querySelectorAll('.error-text');
        errores.forEach(function(e) { e.remove(); });
        let error = document.createElement('div');
        error.className = 'error-text';
        error.textContent = mensaje;
        campo.parentNode.appendChild(error);
    }

    // Validación de otros campos en tiempo real, incluyendo reglas específicas
    function validarCamposRestantes() {
        let esValido = true;
        const campos = form.querySelectorAll('input, select, textarea');
        let diasMin = null, diasMax = null, diasCancelTotal = null, diasCancelParcial = null, porcentajeReembolsoParcial = null;
        let errorEnCancelTotal = false;
        let errorEnCancelParcial = false;
        campos.forEach(function(campo) {
            if (campo === nombreInput) return;
            if (campo.type === 'hidden') return;
            campo.classList.remove('is-invalid');
            // Elimina todos los errores previos de este campo
            let errores = campo.parentNode.querySelectorAll('.error-text');
            errores.forEach(function(e) { e.remove(); });

            switch (campo.name) {
                case 'dias_alquiler_min':
                case 'dias_alquiler_max':
                case 'dias_cancelacion_total':
                case 'dias_cancelacion_parcial':
                    if (!campo.value.trim()) {
                        mostrarErrorUnico(campo, 'Este campo es obligatorio.');
                        esValido = false;
                        if (campo.name === 'dias_cancelacion_total') errorEnCancelTotal = true;
                        if (campo.name === 'dias_cancelacion_parcial') errorEnCancelParcial = true;
                    } else if (contieneDecimal(campo.value)) {
                        mostrarErrorUnico(campo, 'Debe ser un número entero.');
                        esValido = false;
                        if (campo.name === 'dias_cancelacion_total') errorEnCancelTotal = true;
                        if (campo.name === 'dias_cancelacion_parcial') errorEnCancelParcial = true;
                    } else if (parseInt(campo.value) <= 0) {
                        mostrarErrorUnico(campo, 'Debe ser mayor a cero.');
                        esValido = false;
                        if (campo.name === 'dias_cancelacion_total') errorEnCancelTotal = true;
                        if (campo.name === 'dias_cancelacion_parcial') errorEnCancelParcial = true;
                    }
                    if (campo.name === 'dias_alquiler_min') diasMin = parseInt(campo.value);
                    if (campo.name === 'dias_alquiler_max') diasMax = parseInt(campo.value);
                    if (campo.name === 'dias_cancelacion_total') diasCancelTotal = parseInt(campo.value);
                    if (campo.name === 'dias_cancelacion_parcial') diasCancelParcial = parseInt(campo.value);
                    break;
                case 'precio_por_dia':
                    if (!campo.value.trim()) {
                        mostrarErrorUnico(campo, 'Este campo es obligatorio.');
                        esValido = false;
                    } else if (parseFloat(campo.value) < 0) {
                        mostrarErrorUnico(campo, 'El precio debe ser mayor o igual a cero.');
                        esValido = false;
                    }
                    break;
                case 'porcentaje_reembolso_parcial':
                    porcentajeReembolsoParcial = parseInt(campo.value);
                    if (!campo.value.trim()) {
                        mostrarErrorUnico(campo, 'Este campo es obligatorio.');
                        esValido = false;
                    } else if (parseInt(campo.value) <= 0 || parseInt(campo.value) >= 100) {
                        mostrarErrorUnico(campo, 'Debe ser mayor a 0 y menor a 100.');
                        esValido = false;
                    }
                    break;
                default:
                    if (campo.required && !campo.value.trim()) {
                        mostrarErrorUnico(campo, 'Este campo es obligatorio.');
                        esValido = false;
                    }
            }
        });
        // Validaciones cruzadas
        if (!errorEnCancelTotal && !errorEnCancelParcial && diasCancelTotal !== null && diasCancelParcial !== null) {
            if (diasCancelParcial >= diasCancelTotal) {
                const campoParcial = form.querySelector('input[name="dias_cancelacion_parcial"]');
                mostrarErrorUnico(campoParcial, 'Los días para reembolso parcial deben ser menores a los días para reembolso total.');
                esValido = false;
            }
        }
        if (diasMin !== null && diasMax !== null && diasMax < diasMin) {
            const campoMax = form.querySelector('input[name="dias_alquiler_max"]');
            mostrarErrorUnico(campoMax, 'La cantidad máxima debe ser mayor o igual a la mínima.');
            esValido = false;
        }
        return esValido;
    }

    function validarFormulario() {
        const nombreValido = validarNombre();
        const restoValido = validarCamposRestantes();
        submitBtn.disabled = !(nombreValido && restoValido);
    }

    // Eventos
    nombreInput.addEventListener('input', validarFormulario);
    form.querySelectorAll('input, select, textarea').forEach(function(campo) {
        if (campo !== nombreInput) {
            campo.addEventListener('input', validarFormulario);
            campo.addEventListener('change', validarFormulario);
        }
    });
}); 