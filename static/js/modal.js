document.addEventListener('DOMContentLoaded', function () {

    // Abre el modal cuando HTMX carga contenido
    document.body.addEventListener('htmx:afterSwap', function (e) {
        if (e.detail.target.id === 'modal-content-area') {
            var el = document.getElementById('travelerModal');
            if (!el.classList.contains('show')) {
                bootstrap.Modal.getOrCreateInstance(el).show();
            }
        }
    });

    // Cierra el modal al recibir el trigger del POST
    document.body.addEventListener('closeModal', function () {
        var el = document.getElementById('travelerModal');
        var modal = bootstrap.Modal.getInstance(el);
        if (modal) modal.hide();
    });

});

document.body.addEventListener('htmx:afterSwap', function(e) {
    var awk = document.querySelector('input[name="awakening_level"]');
    if (awk) {
        awk.addEventListener('input', function() {
            var msg = document.getElementById('trust-accessory-msg');
            if (msg) msg.style.display = this.value == 4 ? 'block' : 'none';
        });
    }
});