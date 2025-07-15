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
        limpiarErrorFecha(inputInicio, errorIdPrefix+'-inicio');
        limpiarErrorFecha(inputFin, errorIdPrefix+'-fin');
        // Validaciones
        if (!fechaInicio) {
            mostrarErrorFecha(inputInicio, 'Este campo es obligatorio.', errorIdPrefix+'-inicio');
            valido = false;
        }
        if (!fechaFin) {
            mostrarErrorFecha(inputFin, 'Este campo es obligatorio.', errorIdPrefix+'-fin');
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
    let chartFact = null;
    btnFact.addEventListener('click', function() {
        if (!validarFechas(inputInicioFact, inputFinFact, btnFact, 'facturacion')) return;
        const fecha_inicio = inputInicioFact.value;
        const fecha_fin = inputFinFact.value;
        totalFact.innerHTML = '';
        graficoFact.innerHTML = '';
        fetch(`/maquinas/persona/estadisticas/?fecha_inicio=${fecha_inicio}&fecha_fin=${fecha_fin}`)
            .then(resp => resp.json())
            .then(data => {
                if (data.error) {
                    graficoFact.innerHTML = `<div class='text-danger'>${data.error}</div>`;
                    totalFact.innerHTML = '';
                    return;
                }
                if (!data.labels || data.labels.length === 0) {
                    graficoFact.innerHTML = `<div class='text-muted'>No hay datos para el período seleccionado.`;
                    totalFact.innerHTML = '';
                    return;
                }
                // Renderizar gráfico de barras
                graficoFact.innerHTML = '<canvas id="chart-facturacion" width="400" height="220"></canvas>';
                const ctx = document.getElementById('chart-facturacion').getContext('2d');
                if (chartFact) chartFact.destroy();
                chartFact = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Facturación',
                            data: data.data,
                            backgroundColor: '#2176d2',
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `$${context.parsed.y.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value.toLocaleString('es-AR', {minimumFractionDigits: 2});
                                    }
                                }
                            }
                        }
                    }
                });
                // Mostrar total
                totalFact.innerHTML = `Total facturado: $<span id="facturacion-total-valor">${data.total.toLocaleString('es-AR', {minimumFractionDigits: 2})}</span>`;
            })
            .catch(() => {
                graficoFact.innerHTML = `<div class='text-danger'>Error al consultar los datos.</div>`;
                totalFact.innerHTML = '';
            });
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
                                '#2176d2', '#4a96f0', '#6bb3ff', '#8cc4ff', '#a6d1ff', '#f7b32b'
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
        const nombreArchivo = `Máquinas más alquiladas - ${fechaInicio} - ${fechaFin}.xlsx`;
        // Obtener datos de la tabla
        const filas = Array.from(document.querySelectorAll('#tabla-maquinas-alquiladas tbody tr'));
        if (filas.length === 0) {
            alert('No hay resultados para descargar.');
            return;
        }
        // Construir datos para Excel
        let csv = 'Máquina Base\tCantidad de alquileres\n';
        filas.forEach(tr => {
            const tds = tr.querySelectorAll('td');
            csv += `${tds[0].innerText}\t${tds[1].innerText}\n`;
        });
        // Convertir a Blob y descargar como .xlsx (en realidad es TSV, pero Excel lo abre bien)
        const blob = new Blob([csv], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
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
}); 