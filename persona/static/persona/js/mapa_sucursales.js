function initMap(centroMapa, sucursalesData) {
    const ZOOM_INICIAL = 13;
    
    // Inicialización del mapa
    const map = L.map('map').setView(centroMapa, ZOOM_INICIAL);

    // Configuración del mapa base
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Configuración del ícono personalizado
    const customIcon = L.icon({
        iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-black.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    function crearContenidoPopup(sucursal) {
        return `
            <div class="custom-popup">
                <h3>${sucursal.direccion}</h3>
                <p><strong>Horarios:</strong><br>
                ${sucursal.horario}</p>
                <p><strong>Teléfono:</strong> ${sucursal.telefono}</p>
                <p><strong>Email:</strong> ${sucursal.email}</p>
            </div>
        `;
    }

    // Agregar marcadores y ajustar el mapa
    if (sucursalesData.length > 0) {
        const bounds = [];
        
        sucursalesData.forEach(sucursal => {
            const marker = L.marker([sucursal.lat, sucursal.lng], {icon: customIcon}).addTo(map);
            marker.bindPopup(crearContenidoPopup(sucursal));
            bounds.push([sucursal.lat, sucursal.lng]);
        });

        map.fitBounds(bounds);
    } else {
        map.setView(centroMapa, ZOOM_INICIAL);
    }

    // Manejo de errores
    map.on('tileerror', function(e) {
        console.error('Error cargando el mapa:', e);
        alert('Hubo un problema cargando el mapa. Por favor, recargue la página.');
    });

    if (!map || !map.getContainer()) {
        console.error('Error inicializando el mapa');
        document.getElementById('map').innerHTML = '<div class="alert alert-danger">Error cargando el mapa. Por favor, recargue la página.</div>';
    }
} 