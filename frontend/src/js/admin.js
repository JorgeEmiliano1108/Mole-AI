// =============================================================================
// Copyright (C) 2024-2026 Mole.AI - All Rights Reserved.
// =============================================================================
// admin.js - CMD Center logic extracted from inline <script> for SoC compliance.
// Handles: view switching, data loading, chart initialization, and button handlers.
// =============================================================================

import * as echarts from 'echarts';
import { apiService } from './modules/api/ApiService.js';

// ============ VIEW SWITCHING LOGIC ===========
const VIEWS = {
    dashboard: 'view-dashboard',
    'iot-fleet': 'view-iot-fleet',
    mlops: 'view-mlops',
    alerts: 'view-alerts'
};

async function switchView(viewKey) {
    // Hide all views
    document.querySelectorAll('.view-container').forEach(el => el.classList.add('hidden'));

    // Show target view
    const target = document.getElementById('view-' + viewKey);
    if (target) target.classList.remove('hidden');

    // Update breadcrumb
    updateBreadcrumb(viewKey);

    // Update sidebar active state
    updateActiveSidebar(viewKey);

    // Load data based on view
    try {
        if (viewKey === 'dashboard') {
            await loadDashboardData();
        } else if (viewKey === 'iot-fleet') {
            await loadIoTData();
        } else if (viewKey === 'mlops') {
            await loadMLOpsData();
        } else if (viewKey === 'alerts') {
            await loadAlertsData();
        }
    } catch (error) {
        console.error('Error loading ' + viewKey + ' data:', error);
    }
}


// ============ DATA LOADING FUNCTIONS ============
async function loadDashboardData() {
    try {
        const data = await apiService.getKPIData();
        if (data && data.kpis) {
            const kpis = data.kpis;
            const plantasEl = document.querySelector('#view-dashboard .data-card:nth-child(1) .text-2xl');
            const alertasEl = document.querySelector('#view-dashboard .data-card:nth-child(2) .text-2xl');
            const onlineEl = document.querySelector('#view-dashboard .data-card:nth-child(3) .text-2xl');
            const precisionEl = document.querySelector('#view-dashboard .data-card:nth-child(4) .text-2xl');

            if (plantasEl && kpis.plantas_escaneadas) plantasEl.textContent = kpis.plantas_escaneadas.toLocaleString();
            if (alertasEl && kpis.alertas_activas !== undefined) alertasEl.textContent = kpis.alertas_activas;
            if (onlineEl && kpis.dispositivos_online) onlineEl.textContent = kpis.dispositivos_online;
            if (precisionEl && kpis.precision_ms1) precisionEl.textContent = kpis.precision_ms1 + '%';
        }
    } catch (error) {
        console.log('Dashboard data loading skipped (API not ready):', error.message);
    }
}

async function loadIoTData() {
    try {
        const data = await apiService.getIoTFleet();
        if (data && data.nodes) {
            console.log('IoT Fleet data loaded:', data.nodes.length, 'nodes');
        }
    } catch (error) {
        console.log('IoT data loading skipped (API not ready):', error.message);
    }
}

async function loadMLOpsData() {
    try {
        const data = await apiService.getMLMetrics();
        if (data && data.metrics) {
            console.log('MLOps data loaded:', data.metrics);
        }
    } catch (error) {
        console.log('MLOps data loading skipped (API not ready):', error.message);
    }
}

async function loadAlertsData() {
    try {
        const data = await apiService.getAlerts();
        if (data && data.alerts) {
            console.log('Alerts data loaded:', data.alerts.length, 'alerts');
        }
    } catch (error) {
        console.log('Alerts data loading skipped (API not ready):', error.message);
    }
}

// ============ BREADCRUMB & SIDEBAR ============
function updateBreadcrumb(viewKey) {
    const breadcrumb = document.getElementById('breadcrumb');
    if (!breadcrumb) return;

    const labels = {
        dashboard: 'Dashboard \u2014 Vista General',
        'iot-fleet': 'Flota IoT \u2014 Monitoreo ESP32',
        mlops: 'MLOps \u2014 Entrenamiento y Fine-Tuning',
        alerts: 'Centro de Alertas \u2014 Gesti\u00f3n'
    };
    breadcrumb.textContent = labels[viewKey] || 'Dashboard \u2014 Vista General';
}

function updateActiveSidebar(viewKey) {
    const sidebarButtons = document.querySelectorAll('#sidebar nav [data-view]');
    sidebarButtons.forEach(btn => {
        btn.classList.remove('text-mole-accent');
        btn.classList.add('text-mole-text-dim');
        const indicator = btn.querySelector('.bg-mole-accent');
        if (indicator) indicator.remove();
    });

    const activeBtn = document.querySelector(`#sidebar nav [data-view="${viewKey}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('text-mole-text-dim');
        activeBtn.classList.add('text-mole-accent');
        const indicator = document.createElement('span');
        indicator.className = 'ml-auto w-1 h-6 bg-mole-accent rounded-full glow-effect';
        activeBtn.appendChild(indicator);
    }
}

// ============ DATETIME UPDATE ===========
function updateDateTime() {
    const now = new Date();
    const dateEl = document.getElementById('current-date');
    const timeEl = document.getElementById('current-time');

    if (dateEl) {
        const formatted = now.toISOString().split('T')[0];
        dateEl.textContent = formatted;
    }
    if (timeEl) {
        const timeStr = now.toTimeString().split(' ')[0];
        timeEl.textContent = timeStr;
    }
}

// ============ CHART INITIALIZATION ============

// Sparklines (KPI Cards)
function initSparklines() {
    const sparkConfig = {
        type: 'line',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { display: false }, y: { display: false } },
            elements: { point: { radius: 0 }, line: { borderWidth: 1.5 } }
        }
    };

    const plantasCtx = document.getElementById('spark-plantas');
    if (plantasCtx) {
        new Chart(plantasCtx, {
            ...sparkConfig,
            data: {
                labels: Array.from({length: 12}, (_, i) => i),
                datasets: [{
                    data: [80, 95, 110, 105, 120, 115, 130, 140, 135, 145, 150, 160],
                    borderColor: '#00FFCC',
                    backgroundColor: 'rgba(0, 255, 204, 0.1)'
                }]
            }
        });
    }

    const alertasCtx = document.getElementById('spark-alertas');
    if (alertasCtx) {
        new Chart(alertasCtx, {
            ...sparkConfig,
            data: {
                labels: Array.from({length: 12}, (_, i) => i),
                datasets: [{
                    data: [4, 3, 5, 4, 3, 2, 3, 4, 3, 2, 3, 3],
                    borderColor: '#ff4d4d',
                    backgroundColor: 'rgba(255, 77, 77, 0.1)'
                }]
            }
        });
    }

    const onlineCtx = document.getElementById('spark-online');
    if (onlineCtx) {
        new Chart(onlineCtx, {
            ...sparkConfig,
            data: {
                labels: Array.from({length: 12}, (_, i) => i),
                datasets: [{
                    data: [6, 7, 8, 7, 8, 9, 8, 8, 7, 8, 8, 8],
                    borderColor: '#00ff00',
                    backgroundColor: 'rgba(0, 255, 0, 0.1)'
                }]
            }
        });
    }

    const precisionCtx = document.getElementById('spark-precision');
    if (precisionCtx) {
        new Chart(precisionCtx, {
            ...sparkConfig,
            data: {
                labels: Array.from({length: 12}, (_, i) => i),
                datasets: [{
                    data: [94.5, 95.0, 95.5, 95.8, 96.0, 96.1, 96.2, 96.2, 96.3, 96.2, 96.2, 96.2],
                    borderColor: '#ffcc00',
                    backgroundColor: 'rgba(255, 204, 0, 0.1)'
                }]
            }
        });
    }
}

// Dashboard Charts (Area + Donut + Bar)
function initDashboardCharts() {
    const areaCtx = document.getElementById('chart-area-scans');
    if (areaCtx) {
        new Chart(areaCtx, {
            type: 'line',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                datasets: [{
                    label: 'Escaneos',
                    data: [120, 190, 300, 500, 200, 300],
                    borderColor: '#00FFCC',
                    backgroundColor: 'rgba(0, 255, 204, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#c0c0c0' } }
                },
                scales: {
                    x: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    const donutCtx = document.getElementById('chart-donut-fleet');
    if (donutCtx) {
        new Chart(donutCtx, {
            type: 'doughnut',
            data: {
                labels: ['Online', 'Warning', 'Offline'],
                datasets: [{
                    data: [8, 2, 2],
                    backgroundColor: ['#00ff00', '#ffcc00', '#ff4d4d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#c0c0c0', padding: 10 } }
                }
            }
        });
    }

    const barCtx = document.getElementById('chart-bar-species');
    if (barCtx) {
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: ['Biznaga', 'Maguey', 'Nopal', 'Lechuguilla', 'Garumbe'],
                datasets: [{
                    label: 'Detecciones',
                    data: [45, 30, 25, 20, 15],
                    backgroundColor: '#00FFCC'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#c0c0c0' } }
                },
                scales: {
                    x: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }
}

// IoT Fleet Radar Chart (ECharts)
function initRadarChart() {
    const radarEl = document.getElementById('chart-radar-health');
    if (radarEl) {
        const chart = echarts.init(radarEl);
        chart.setOption({
            radar: {
                indicator: [
                    { name: 'Bater\u00eda', max: 100 },
                    { name: 'Se\u00f1al', max: 100 },
                    { name: 'Temp', max: 80 },
                    { name: 'Uptime', max: 100 },
                    { name: 'Latencia', max: 500 }
                ],
                axisName: { color: '#c0c0c0' },
                splitArea: { areaStyle: { color: ['rgba(0,255,204,0.05)', 'rgba(0,255,204,0.02)'] } }
            },
            series: [{
                type: 'radar',
                data: [{
                    value: [85, 92, 45, 98, 120],
                    name: 'Promedio Fleet',
                    areaStyle: { color: 'rgba(0,255,204,0.3)' },
                    lineStyle: { color: '#00FFCC' }
                }]
            }]
        });
    }
}

// MLOps Training Chart (ECharts)
function initTrainingChart() {
    const trainingEl = document.getElementById('chart-line-training');
    if (trainingEl) {
        const chart = echarts.init(trainingEl);
        chart.setOption({
            xAxis: {
                type: 'category',
                data: ['Epoch 1', 'Epoch 2', 'Epoch 3', 'Epoch 4', 'Epoch 5'],
                axisLabel: { color: '#c0c0c0' }
            },
            yAxis: {
                type: 'value',
                axisLabel: { color: '#c0c0c0' }
            },
            series: [{
                data: [0.72, 0.85, 0.92, 0.96, 0.962],
                type: 'line',
                smooth: true,
                lineStyle: { color: '#00FFCC' },
                areaStyle: { color: 'rgba(0,255,204,0.2)' }
            }],
            grid: { left: '10%', right: '10%', bottom: '15%' }
        });
    }
}

// ============ BUTTON HANDLER FUNCTIONS (CLEAN) ============

// Export data
function handleExport() {
    if (apiService && typeof apiService.exportData === 'function') {
        apiService.exportData().catch(e => {
            console.error('Export failed:', e);
            alert('Error al exportar datos: ' + (e.message || e));
        });
    } else {
        console.warn('ApiService.exportData not available');
    }
}

// Start new training
function handleNewTraining() {
    if (!window.confirm('\u00bfIniciar nuevo entrenamiento ML?')) return;

    if (apiService && typeof apiService.triggerTraining === 'function') {
        apiService.triggerTraining({
            model_type: 'MS1',
            epochs: 50,
            learning_rate: 0.001
        }).catch(e => {
            console.error('Training failed:', e);
            alert('Error al iniciar entrenamiento: ' + (e.message || e));
        });
    } else {
        console.warn('ApiService.triggerTraining not available');
    }
}

// Deploy model
function handleDeploy(modelId) {
    if (!window.confirm('\u00bfDesplegar modelo ' + modelId + ' a producci\u00f3n?')) return;

    if (apiService && typeof apiService.deployModel === 'function') {
        apiService.deployModel({
            model_id: modelId
        }).catch(e => {
            console.error('Deploy failed:', e);
            alert('Error al desplegar modelo: ' + (e.message || e));
        });
    } else {
        console.warn('ApiService.deployModel not available');
    }
}

// Acknowledge alert
function handleAcknowledge(alertId) {
    if (apiService && typeof apiService.acknowledgeAlert === 'function') {
        apiService.acknowledgeAlert(alertId).catch(e => {
            console.error('Acknowledge failed:', e);
            alert('Error al reconocer alerta: ' + (e.message || e));
        });
    } else {
        console.warn('ApiService.acknowledgeAlert not available');
    }
}

// Delete alert
function handleDelete(alertId) {
    if (!window.confirm('\u00bfEliminar alerta ' + alertId + '?')) return;

    if (apiService && typeof apiService.deleteAlert === 'function') {
        apiService.deleteAlert(alertId).catch(e => {
            console.error('Delete failed:', e);
            alert('Error al eliminar alerta: ' + (e.message || e));
        });
    } else {
        console.warn('ApiService.deleteAlert not available');
    }
}

// ============ EVENT DELEGATION (CSP-Compliant) ============
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;
    const target = btn.dataset.target;
    const id = btn.dataset.id;

    switch (action) {
        case 'switch-view':
            switchView(target);
            break;
        case 'export':
            handleExport();
            break;
        case 'new-training':
            handleNewTraining();
            break;
        case 'deploy':
            handleDeploy(target);
            break;
        case 'acknowledge':
            handleAcknowledge(id);
            break;
        case 'delete-alert':
            handleDelete(id);
            break;
        case 'navigate':
            window.location.replace(target);
            break;
        default:
            break;
    }
});

// ============ INITIALIZATION ============
updateDateTime();
setInterval(updateDateTime, 1000);
switchView('dashboard'); // Default view

// Initialize all charts after DOM loaded
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        initSparklines();
        initDashboardCharts();
        initRadarChart();
        initTrainingChart();
    }, 100);
});
