/* ============================================================
   CotC Equip II - Charts
   Requiere: Chart.js cargado antes que este archivo
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    const donutDefaults = {
        type: 'doughnut',
        options: {
            cutout: '72%',
            responsive: true,
            animation: { animateRotate: true, duration: 800 },
            plugins: {
                legend:  { display: false },
                tooltip: { enabled: false },
            },
        }
    };

    // ── Donut: Reclutados ─────────────────────────────────
    const elReclutados = document.getElementById('chart-reclutados');
    if (elReclutados) {
        const reclutados   = parseInt(elReclutados.dataset.value);
        const reconocidos  = parseInt(elReclutados.dataset.total);
        new Chart(elReclutados, {
            ...donutDefaults,
            data: {
                datasets: [{
                    data: [reclutados, reconocidos - reclutados],
                    backgroundColor: ['#c9a84c', '#35354a'],
                    borderWidth: 0,
                    hoverOffset: 0,
                }]
            }
        });
    }

    // ── Donut: 6 Estrellas ────────────────────────────────
    const elSeis = document.getElementById('chart-seis-estrellas');
    if (elSeis) {
        const seis        = parseInt(elSeis.dataset.value);
        const reconocidos = parseInt(elSeis.dataset.total);
        new Chart(elSeis, {
            ...donutDefaults,
            data: {
                datasets: [{
                    data: [seis, reconocidos - seis],
                    backgroundColor: ['#c084fc', '#35354a'],
                    borderWidth: 0,
                    hoverOffset: 0,
                }]
            }
        });
    }

});