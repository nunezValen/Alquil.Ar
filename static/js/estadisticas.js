// JS para validación de fechas y manejo de consultas en estadísticas

document.addEventListener('DOMContentLoaded', function() {
    // --- Facturación ---
    const formFact = document.getElementById('form-facturacion');
    const btnFact = document.getElementById('btn-consultar-facturacion');
    const inputInicioFact = formFact.querySelector('input[name="fecha_inicio"]');
    const inputFinFact = formFact.querySelector('input[name="fecha_fin"]');
    const totalFact = document.getElementById('facturacion-total');
    const graficoFact = document.getElementById('facturacion-grafico');

    // --- Máquinas ---
    const formMaq = document.getElementById('form-maquinas');
    const btnMaq = document.getElementById('btn-consultar-maquinas');
    const inputInicioMaq = formMaq.querySelector('input[name="fecha_inicio"]');
    const inputFinMaq = formMaq.querySelector('input[name="fecha_fin"]');
    const graficoMaq = document.getElementById('maquinas-grafico-torta');
    const listaMaq = document.getElementById('maquinas-lista-resultados');

    // Utilidad para formatear fecha a YYYY-MM-DD
    function getFecha(input) {
        return input.value ? new Date(input.value) : null;
    }
    function hoyISO() {
        const hoy = new Date();
        return hoy.toISOString().slice(0,10);
    }

    // Validación de fechas
    function mostrarErrorFecha(input, msg, errorIdPrefix) {
        let errorDiv = document.getElementById(errorIdPrefix+'-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.id = errorIdPrefix+'-error';
            input.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = msg;
        input.classList.add('is-invalid');
    }
    function limpiarErrorFecha(input, errorIdPrefix) {
        let errorDiv = document.getElementById(errorIdPrefix+'-error');
        if (errorDiv) errorDiv.remove();
        input.classList.remove('is-invalid');
    }
    function validarFechas(inputInicio, inputFin, btn, errorIdPrefix) {
        let valido = true;
        const fechaInicio = getFecha(inputInicio);
        const fechaFin = getFecha(inputFin);
        const hoy = new Date(hoyISO());
        limpiarErrorFecha(inputInicio, errorIdPrefix+'-inicio');
        limpiarErrorFecha(inputFin, errorIdPrefix+'-fin');
        // Validaciones
        if (!fechaInicio) {
            mostrarErrorFecha(inputInicio, 'Este campo es obligatorio.', errorIdPrefix+'-inicio');
            valido = false;
        } else if (fechaInicio > hoy) {
            mostrarErrorFecha(inputInicio, 'La fecha no puede ser futura.', errorIdPrefix+'-inicio');
            valido = false;
        }
        if (!fechaFin) {
            mostrarErrorFecha(inputFin, 'Este campo es obligatorio.', errorIdPrefix+'-fin');
            valido = false;
        } else if (fechaFin > hoy) {
            mostrarErrorFecha(inputFin, 'La fecha no puede ser futura.', errorIdPrefix+'-fin');
            valido = false;
        }
        if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
            mostrarErrorFecha(inputFin, 'La fecha de fin debe ser igual o posterior a la de inicio.', errorIdPrefix+'-fin');
            valido = false;
        }
        btn.disabled = !valido;
        return valido;
    }

    // Eventos de validación en Facturación
    [inputInicioFact, inputFinFact].forEach(input => {
        input.addEventListener('input', function() {
            validarFechas(inputInicioFact, inputFinFact, btnFact, 'facturacion');
        });
    });
    // Eventos de validación en Máquinas
    [inputInicioMaq, inputFinMaq].forEach(input => {
        input.addEventListener('input', function() {
            validarFechas(inputInicioMaq, inputFinMaq, btnMaq, 'maquinas');
        });
    });

    // --- Consulta Facturación ---
    btnFact.addEventListener('click', function() {
        if (!validarFechas(inputInicioFact, inputFinFact, btnFact, 'facturacion')) return;
        // Aquí iría la consulta AJAX real
        // Simulación de resultado:
        totalFact.innerHTML = 'Total facturado: $<span id="facturacion-total-valor">999999</span>';
        graficoFact.innerHTML = '';
        // Aquí se podría insertar una imagen de gráfico generada por el backend
    });

    // --- Consulta Máquinas ---
    let chartMaq = null;
    btnMaq.addEventListener('click', function() {
        if (!validarFechas(inputInicioMaq, inputFinMaq, btnMaq, 'maquinas')) return;
        const fecha_inicio = inputInicioMaq.value;
        const fecha_fin = inputFinMaq.value;
        graficoMaq.innerHTML = '';
        listaMaq.innerHTML = '';
        fetch(`/persona/estadisticas/maquinas/?fecha_inicio=${fecha_inicio}&fecha_fin=${fecha_fin}`)
            .then(resp => resp.json())
            .then(data => {
                if (data.error) {
                    graficoMaq.innerHTML = `<div class='text-danger'>${data.error}</div>`;
                    return;
                }
                if (!data.labels || data.labels.length === 0) {
                    graficoMaq.innerHTML = `<div class='text-muted'>No hay datos para el período seleccionado.</div>`;
                    return;
                }
                // Render gráfico de torta
                graficoMaq.innerHTML = '<canvas id="chart-maquinas" width="400" height="260"></canvas>';
                const ctx = document.getElementById('chart-maquinas').getContext('2d');
                if (chartMaq) chartMaq.destroy();
                chartMaq = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.cantidades,
                            backgroundColor: [
                                '#2176d2', '#51a3f5', '#7bcfff', '#b3e0ff', '#f7b32b'
                            ],
                        }]
                    },
                    options: {
                        plugins: {
                            legend: { position: 'right' }
                        }
                    }
                });
                // Render listado en tabla
                listaMaq.innerHTML = '';
                data.listado.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${item.nombre}</td><td class='text-end'>${item.cantidad}</td>`;
                    listaMaq.appendChild(tr);
                });
            })
            .catch(() => {
                graficoMaq.innerHTML = `<div class='text-danger'>Error al consultar los datos.</div>`;
            });
    });

    // --- Descargar resultados de máquinas como Excel ---
    document.getElementById('btn-descargar-maquinas').addEventListener('click', function() {
        const fechaInicio = inputInicioMaq.value;
        const fechaFin = inputFinMaq.value;
        const nombreArchivo = `Maquinas_mas_alquiladas_${fechaInicio || 'inicio'}_${fechaFin || 'hoy'}.csv`;
        // Obtener datos de la tabla
        const filas = Array.from(document.querySelectorAll('#tabla-maquinas-alquiladas tbody tr'));
        if (filas.length === 0) {
            alert('No hay resultados para descargar.');
            return;
        }
        // Construir datos para Excel
        let csv = 'Maquina Base,Cantidad de alquileres\r\n';
        filas.forEach(tr => {
            const tds = tr.querySelectorAll('td');
            csv += `"${tds[0].innerText.replace(/"/g,'""')}",${tds[1].innerText}\r\n`;
        });
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = nombreArchivo;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    });

    // -----------------------------
    // --- CLIENTES ---------------
    // -----------------------------

    const formCli = document.getElementById('form-clientes');
    const btnCli = document.getElementById('btn-consultar-clientes');
    const inputInicioCli = formCli.querySelector('input[name="fecha_inicio"]');
    const inputFinCli = formCli.querySelector('input[name="fecha_fin"]');
    const graficoCli = document.getElementById('clientes-grafico');
    const listaCli = document.getElementById('clientes-lista-resultados');

    // Validación opcional de fechas
    function validarFechasOpcionales(inputInicio, inputFin, btn, prefix) {
        let valido = true;
        const fechaInicio = getFecha(inputInicio);
        const fechaFin = getFecha(inputFin);
        limpiarErrorFecha(inputInicio, prefix + '-inicio');
        limpiarErrorFecha(inputFin, prefix + '-fin');
        if (!inputInicio.checkValidity()) {
            mostrarErrorFecha(inputInicio, 'La fecha ingresada no es válida.', prefix + '-inicio');
            valido = false;
        }
        if (!inputFin.checkValidity()) {
            mostrarErrorFecha(inputFin, 'La fecha ingresada no es válida.', prefix + '-fin');
            valido = false;
        }
        
        if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
            mostrarErrorFecha(inputFin, 'La fecha de fin debe ser igual o posterior a la de inicio.', prefix + '-fin');
            valido = false;
        }
        btn.disabled = !valido;
        return valido;
    }

    [inputInicioCli, inputFinCli].forEach(inp => {
        inp.addEventListener('input', () => {
            validarFechasOpcionales(inputInicioCli, inputFinCli, btnCli, 'clientes');
        });
    });

    let chartCli = null;
    btnCli.addEventListener('click', function() {
        if (!validarFechasOpcionales(inputInicioCli, inputFinCli, btnCli, 'clientes')) return;

        const fecha_inicio = inputInicioCli.value;
        const fecha_fin = inputFinCli.value;

        graficoCli.innerHTML = '';
        listaCli.innerHTML = '';

        const params = new URLSearchParams();
        if (fecha_inicio) params.append('fecha_inicio', fecha_inicio);
        if (fecha_fin) params.append('fecha_fin', fecha_fin);

        fetch(`/persona/estadisticas/clientes/?${params.toString()}`)
            .then(resp => resp.json())
            .then(data => {
                if (data.error) {
                    graficoCli.innerHTML = `<div class='text-danger'>${data.error}</div>`;
                    return;
                }
                if (!data.labels || data.labels.length === 0) {
                    graficoCli.innerHTML = `<div class='text-muted'>No hay datos para el período seleccionado.</div>`;
                    return;
                }

                // Crear contenedor deslizante
                graficoCli.innerHTML = '<div style="overflow-x:auto; width:100%;"><canvas id="chart-clientes" height="260"></canvas></div>';
                const canvas = document.getElementById('chart-clientes');
                const ctx = canvas.getContext('2d');
                const width = Math.max(400, data.labels.length * 60);
                canvas.width = width;

                if (chartCli) chartCli.destroy();
                chartCli = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.cantidades,
                            backgroundColor: '#2176d2'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });

                // Render tabla
                data.listado.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${item.nombre}</td><td>${item.email}</td><td class='text-end'>${item.cantidad}</td>`;
                    listaCli.appendChild(tr);
                });
            })
            .catch(() => {
                graficoCli.innerHTML = `<div class='text-danger'>Error al consultar los datos.</div>`;
            });
    });

    // Descargar clientes
    document.getElementById('btn-descargar-clientes').addEventListener('click', function() {
        const params = new URLSearchParams();
        if (inputInicioCli.value) params.append('fecha_inicio', inputInicioCli.value);
        if (inputFinCli.value)   params.append('fecha_fin', inputFinCli.value);
        params.append('export', 'xlsx');
        // Redirigir para que el navegador descargue el archivo generado por el backend
        window.location.href = `/persona/estadisticas/clientes/?${params.toString()}`;
    });
}); 