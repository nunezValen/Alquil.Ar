// Lógica de filtros para el catálogo de máquinas

document.addEventListener('DOMContentLoaded', function() {
    // --- Slider de precio ---
    const slider = document.getElementById('slider-precio');
    const inputMin = document.getElementById('precio_min');
    const inputMax = document.getElementById('precio_max');
    const min = parseFloat(inputMin.value);
    const max = parseFloat(inputMax.value);
    // Si min y max son iguales, forzar un rango de 1
    const sliderMin = min === max ? min - 1 : min;
    const sliderMax = min === max ? max + 1 : max;
    const minLabel = document.getElementById('precio-min-label');
    const maxLabel = document.getElementById('precio-max-label');

    if (slider) {
        noUiSlider.create(slider, {
            start: [min, max],
            connect: true,
            step: 1,
            range: {
                'min': sliderMin,
                'max': sliderMax
            },
            tooltips: false, // Quitar tooltips
            format: {
                to: function (value) { return Math.round(value); },
                from: function (value) { return Number(value); }
            }
        });
        slider.noUiSlider.on('update', function(values) {
            inputMin.value = values[0];
            inputMax.value = values[1];
            minLabel.textContent = `$${values[0]}`;
            maxLabel.textContent = `$${values[1]}`;
        });
        slider.noUiSlider.on('change', function() {
            recargarGrilla();
        });
    }

    // --- Filtros checkboxes ---
    document.querySelectorAll('.filtro-tipo, .filtro-marca, .filtro-estado').forEach(cb => {
        cb.addEventListener('change', recargarGrilla);
    });

    // --- Limpiar filtros ---
    const limpiarBtn = document.getElementById('limpiar-filtros');
    if (limpiarBtn) {
        limpiarBtn.addEventListener('click', function() {
            document.querySelectorAll('.filtro-tipo, .filtro-marca, .filtro-estado').forEach(cb => cb.checked = false);
            if (slider) {
                slider.noUiSlider.set([min, max]);
            }
            recargarGrilla();
        });
    }

    // --- Recarga AJAX de la grilla ---
    function recargarGrilla() {
        const params = new URLSearchParams();
        // Tipos
        document.querySelectorAll('.filtro-tipo:checked').forEach(cb => params.append('tipo', cb.value));
        // Marcas
        document.querySelectorAll('.filtro-marca:checked').forEach(cb => params.append('marca', cb.value));
        // Estado
        document.querySelectorAll('.filtro-estado:checked').forEach(cb => params.append('estado', cb.value));
        // Precio
        params.append('precio_min', inputMin.value);
        params.append('precio_max', inputMax.value);
        // Búsqueda
        const q = document.querySelector('input[name="q"]');
        if (q && q.value) params.append('q', q.value);
        fetch(`/maquinas/catalogo/grilla/?${params.toString()}`)
            .then(resp => resp.json())
            .then(data => {
                document.getElementById('catalogo-grilla').innerHTML = data.html;
            });
    }
}); 