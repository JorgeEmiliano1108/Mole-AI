const deviceId = localStorage.getItem('moleia_device_id');
if (deviceId) {
    const btn = document.getElementById('health-toggle-sre');
    if (btn) btn.style.display = '';
}
window.addEventListener('deviceLinked', function () {
    const btn = document.getElementById('health-toggle-sre');
    if (btn) btn.style.display = '';
});
