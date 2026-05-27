// ==========================================================
// IoT Provisioning - Tabs, Web Bluetooth & Wi-Fi binding
// ==========================================================

//    BLE GATT UUIDs (must match ESP32 firmware)               
const BLE_SERVICE_UUID    = '0000fee0-0000-1000-8000-00805f9b34fb';
const CHAR_SSID_UUID      = '0000abce-0000-1000-8000-00805f9b34fb';
const CHAR_PASS_UUID      = '0000abcf-0000-1000-8000-00805f9b34fb';
const CHAR_TOKEN_UUID     = '0000abd0-0000-1000-8000-00805f9b34fb';
const CHAR_STATUS_UUID    = '0000abd1-0000-1000-8000-00805f9b34fb';

let _selectedBleDevice = null;
let _bleServer         = null;

//    Tab Switching                                            
export function initIoTView() {
    // ---- DIAGNOSTIC LOGS ----
    console.info('[DIAG] initIoTView called. navigator.bluetooth?', !!navigator.bluetooth);
    console.info('[DIAG] Current protocol:', location.protocol);
    // -------------------------
    const tabWifi  = document.getElementById('tab-wifi');
    const tabBle   = document.getElementById('tab-ble');
    const panelW   = document.getElementById('panel-wifi');
    const panelB   = document.getElementById('panel-ble');

    if (!tabWifi || !tabBle) return;

    // Prevent double-init
    if (tabWifi.dataset.iotInit) return;
    tabWifi.dataset.iotInit = '1';

    const activeTab   = 'bg-mole-cyan text-mole-base';
    const inactiveTab = 'bg-mole-surface text-mole-dim hover:text-mole-cyan';
    const baseTab     = 'flex-1 py-2.5 text-xs font-bold tracking-widest transition-colors';

    tabWifi.addEventListener('click', () => {
        tabWifi.className  = `${baseTab} ${activeTab}`;
        tabBle.className   = `${baseTab} ${inactiveTab}`;
        panelW.classList.remove('hidden');
        panelB.classList.add('hidden');
    });

    tabBle.addEventListener('click', () => {
        tabBle.className   = `${baseTab} ${activeTab}`;
        tabWifi.className  = `${baseTab} ${inactiveTab}`;
        panelB.classList.remove('hidden');
        panelW.classList.add('hidden');
    });

    //    BLE Scan Button                                      
    const btnScan = document.getElementById('btn-ble-scan');
    if (btnScan) btnScan.addEventListener('click', startBleScan);

    //    BLE Bind Button                                      
    const btnProvBle = document.getElementById('btn-prov-ble');
    if (btnProvBle) btnProvBle.addEventListener('click', provisionViaBle);

    //    Wi-Fi Bind Button                                    
    const btnProvWifi = document.getElementById('btn-prov-wifi');
    if (btnProvWifi) btnProvWifi.addEventListener('click', provisionViaWifi);
}

//    Status Helper                                            
function setStatus(msg, type = 'info') {
    const container = document.getElementById('prov-status');
    const text      = document.getElementById('prov-status-text');
    if (!container || !text) return;

    container.classList.remove('hidden');
    text.textContent = msg;

    const colorMap = {
        info:    'text-mole-cyan',
        success: 'text-mole-green',
        error:   'text-mole-red',
        loading: 'text-mole-cyan animate-pulse',
    };
    text.className = `${colorMap[type] || colorMap.info} text-xs font-mono`;
}

//    Web Bluetooth Scan                                       
async function startBleScan() {
    // ---- DIAGNOSTIC LOGS ----
    console.info('[DIAG] navigator.bluetooth available:', !!navigator.bluetooth);
    console.info('[DIAG] page protocol:', location.protocol);
    if (location.protocol !== 'https:') {
        console.warn('[DIAG] Insecure context: Web Bluetooth requires HTTPS or localhost.');
        setStatus('ADVERTENCIA: Esta p\u00e1gina no est\u00e1 en HTTPS; Web Bluetooth puede estar bloqueado.', 'error');
    }
    // -------------------------
    const list = document.getElementById('ble-device-list');
    const btnBind = document.getElementById('btn-prov-ble');
    if (!list) return;

    if (!navigator.bluetooth) {
        setStatus('ERROR: Web Bluetooth no soportado. Use Chrome/Edge.', 'error');
        return;
    }

    setStatus('Escaneando dispositivos Bluetooth...', 'loading');
    list.innerHTML = '<p class="text-mole-cyan text-[10px] font-mono text-center py-4 animate-pulse">SCANNING...</p>';

    try {
        const device = await navigator.bluetooth.requestDevice({
            filters: [{ namePrefix: 'Mole_OpenClaw' }],
            optionalServices: [BLE_SERVICE_UUID],
        });

        _selectedBleDevice = device;

        list.innerHTML = `
            <div class="flex items-center justify-between p-2.5 bg-mole-bg border-2 border-mole-cyan rounded transition-colors">
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 bg-mole-green rounded-full animate-pulse"></span>
                    <span class="text-mole-text text-xs font-mono">${device.name || 'ESP32 Node'}</span>
                </div>
                <span class="text-mole-cyan text-[10px] font-mono">${device.id?.slice(0, 17) || 'PAIRED'}</span>
            </div>
        `;

        if (btnBind) {
            btnBind.disabled = false;
            btnBind.classList.remove('disabled:opacity-30');
        }
        setStatus('Dispositivo seleccionado: ' + device.name, 'success');

    } catch (err) {
        if (err.name === 'NotFoundError') {
            list.innerHTML = '<p class="text-mole-dim text-[10px] font-mono text-center py-4">[ Ning\u00fan dispositivo seleccionado ]</p>';
            setStatus('Escaneo cancelado por el usuario.', 'info');
        } else {
            setStatus('Error BLE: ' + err.message, 'error');
        }
    }
}

//    BLE Provisioning (GATT Write)                            
async function provisionViaBle() {
    if (!_selectedBleDevice) {
        setStatus('ERROR: Ning\u00fan dispositivo seleccionado.', 'error');
        return;
    }

    const ssid  = (document.getElementById('prov-ssid')?.value || '').trim();
    const pass  = (document.getElementById('prov-pass')?.value || '').trim();
    const token = window.getAuthToken ? window.getAuthToken() : '';

    if (!ssid || !pass) {
        setStatus('ERROR: Ingrese SSID y contrase\u00f1a en la pesta\u00f1a Wi-Fi primero.', 'error');
        return;
    }

    setStatus('Conectando via GATT...', 'loading');
    const encoder = new TextEncoder();

    try {
        _bleServer = await _selectedBleDevice.gatt.connect();
        const service = await _bleServer.getPrimaryService(BLE_SERVICE_UUID);

        const charSsid = await service.getCharacteristic(CHAR_SSID_UUID);
        await charSsid.writeValue(encoder.encode(ssid));

        const charPass = await service.getCharacteristic(CHAR_PASS_UUID);
        await charPass.writeValue(encoder.encode(pass));

        if (token) {
            const charToken = await service.getCharacteristic(CHAR_TOKEN_UUID);
            await charToken.writeValue(encoder.encode(token));
        }

        const charStatus = await service.getCharacteristic(CHAR_STATUS_UUID);
        await charStatus.startNotifications();
        charStatus.addEventListener('characteristicvaluechanged', (event) => {
            const decoder = new TextDecoder();
            const status  = decoder.decode(event.target.value);
            if (status === 'OK') {
                setStatus('ESP32 conectado a WiFi. Vinculacion exitosa.', 'success');
            } else {
                setStatus('ESP32 reporto: ' + status, 'error');
            }
        });

        setStatus('Credenciales enviadas. Esperando respuesta del ESP32...', 'loading');

    } catch (err) {
        setStatus('Error GATT: ' + err.message, 'error');
        if (_bleServer) {
            try { _bleServer.disconnect(); } catch (_) { /* noop */ }
        }
    }
}

//    Wi-Fi Provisioning (API Backend)                         
async function provisionViaWifi() {
    const ssid     = (document.getElementById('prov-ssid')?.value || '').trim();
    const pass     = (document.getElementById('prov-pass')?.value || '').trim();
    const nodeName = (document.getElementById('prov-node-name')?.value || '').trim();

    if (!ssid || !pass) {
        setStatus('ERROR: SSID y contrase\u00f1a son obligatorios.', 'error');
        return;
    }

    setStatus('Registrando nodo en el backend...', 'loading');

    try {
        const payload = {
            node_name: nodeName || ('ESP32_' + Date.now().toString(36).toUpperCase()),
            wifi_ssid: ssid,
        };

        await window.ApiService.post('iot/nodes/', payload);
        setStatus('Nodo "' + payload.node_name + '" registrado en la plataforma.', 'success');

    } catch (err) {
        setStatus('Error al registrar nodo: ' + (err.message || err), 'error');
    }
}

// Expose globally for navigation hook
window.initIoTView = initIoTView;
