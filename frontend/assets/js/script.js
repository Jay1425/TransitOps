/* ============================================================
   TRANSITOPS ERP - SHARED SCRIPT ENGINE
   Lucide Activation, Notification Dropdowns, & Chart Bindings
============================================================ */

const MOCK_CREDENTIALS = {
  fleet_manager: {
    name: 'Alex Morgan',
    roleLabel: 'Fleet Manager',
    dashboardUrl: '../fleet_manager/dashboard.html'
  },
  driver: {
    name: 'Marcus Davis',
    roleLabel: 'Driver',
    dashboardUrl: '../driver/dashboard.html'
  },
  safety_officer: {
    name: 'Sarah Chen',
    roleLabel: 'Safety Officer',
    dashboardUrl: '../safety_officer/dashboard.html'
  },
  finance: {
    name: 'Jordan Wells',
    roleLabel: 'Financial Analyst',
    dashboardUrl: '../finance/dashboard.html'
  }
};

// Mock Session Routing
function performMockLogin(role) {
  if (MOCK_CREDENTIALS[role]) {
    localStorage.setItem('userRole', role);
    localStorage.setItem('userName', MOCK_CREDENTIALS[role].name);
    localStorage.setItem('roleLabel', MOCK_CREDENTIALS[role].roleLabel);
    window.location.href = MOCK_CREDENTIALS[role].dashboardUrl;
  }
}

function verifyAccessGuard(requiredRole) {
  const currentRole = localStorage.getItem('userRole');
  if (!currentRole) {
    window.location.href = '../auth/login.html';
    return;
  }
  if (requiredRole && currentRole !== requiredRole) {
    alert('Access Denied: Restrained area.');
    window.location.href = MOCK_CREDENTIALS[currentRole].dashboardUrl;
  }
}

function terminateMockSession() {
  localStorage.removeItem('userRole');
  localStorage.removeItem('userName');
  localStorage.removeItem('roleLabel');
  window.location.href = '../auth/login.html';
}

// Global UI Events
document.addEventListener('DOMContentLoaded', () => {
  // Trigger Lucide Icons Rendering
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

  // Restore profiles text
  const userTextEl = document.getElementById('session-user-name');
  const roleTextEl = document.getElementById('session-user-role');
  
  if (userTextEl) userTextEl.textContent = localStorage.getItem('userName') || 'Demo User';
  if (roleTextEl) roleTextEl.textContent = localStorage.getItem('roleLabel') || 'Staff';

  // Collapsible Sidebar Toggle
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  const toggleBtn = document.getElementById('sidebar-toggle');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      if (window.innerWidth >= 1024) {
        sidebar.classList.toggle('sidebar-collapsed');
        if (mainContent) {
          mainContent.classList.toggle('lg:pl-[68px]');
          mainContent.classList.toggle('lg:pl-64');
        }
      } else {
        sidebar.classList.toggle('mobile-open');
      }
    });
  }

  // Notification Bell Dropdown
  const bellBtn = document.getElementById('bell-button');
  const bellDropdown = document.getElementById('bell-dropdown');
  if (bellBtn && bellDropdown) {
    bellBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      bellDropdown.classList.toggle('active');
      const profileMenu = document.getElementById('profile-dropdown');
      if (profileMenu) profileMenu.classList.remove('active');
    });
  }

  // Profile Menu Dropdown
  const profileBtn = document.getElementById('profile-menu-button');
  const profileMenu = document.getElementById('profile-dropdown');

  if (profileBtn && profileMenu) {
    profileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      profileMenu.classList.toggle('active');
      if (bellDropdown) bellDropdown.classList.remove('active');
    });
  }

  document.addEventListener('click', () => {
    if (profileMenu) profileMenu.classList.remove('active');
    if (bellDropdown) bellDropdown.classList.remove('active');
  });

  // Initialize charts dynamically based on elements presence
  initializeSystemCharts();
});

// Toast Notifications System
function triggerToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-3';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const colors = {
    success: 'border-l-4 border-l-green-500',
    warning: 'border-l-4 border-l-amber-500',
    danger: 'border-l-4 border-l-red-500',
    info: 'border-l-4 border-l-blue-500'
  };

  toast.className = `bg-white text-slate-800 px-4 py-3 rounded shadow-md border border-slate-200 min-w-[280px] flex items-center gap-3 animate-fade-in ${colors[type] || colors.success}`;
  toast.innerHTML = `<span class="text-xs font-semibold flex-1">${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'all 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Chart.js Configuration
function initializeSystemCharts() {
  const fontOptions = { family: 'Inter', size: 10 };
  const gridLineColor = '#F1F5F9';
  const tickColor = '#64748B';

  const chartScales = {
    x: { ticks: { color: tickColor, font: fontOptions }, grid: { display: false } },
    y: { ticks: { color: tickColor, font: fontOptions }, grid: { color: gridLineColor } }
  };

  // Fleet Status Distribution Donut
  const fs = document.getElementById('fleet-status-chart');
  if (fs) {
    new Chart(fs, {
      type: 'doughnut',
      data: {
        labels: ['Available', 'On Trip', 'Maintenance', 'Delayed'],
        datasets: [{
          data: [89, 34, 12, 13],
          backgroundColor: ['#22c55e', '#2563eb', '#f59e0b', '#ef4444'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { font: fontOptions } } },
        cutout: '72%'
      }
    });
  }

  // Vehicle Distribution by Type Bar
  const vd = document.getElementById('vehicle-dist-chart');
  if (vd) {
    new Chart(vd, {
      type: 'bar',
      data: {
        labels: ['Trucks', 'Trailers', 'Vans', 'Tankers', 'Buses'],
        datasets: [{
          data: [52, 38, 29, 18, 11],
          backgroundColor: '#2563eb',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: chartScales
      }
    });
  }

  // Driver Fuel logs line chart
  const df = document.getElementById('driver-fuel-chart');
  if (df) {
    new Chart(df, {
      type: 'line',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
          data: [18, 22, 19, 25, 21, 23, 20],
          borderColor: '#22c55e',
          backgroundColor: 'rgba(34, 197, 94, 0.05)',
          tension: 0.3,
          fill: true,
          pointBackgroundColor: '#22c55e'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: chartScales
      }
    });
  }

  // Safety Score line charts
  const ss = document.getElementById('safety-score-chart');
  if (ss) {
    new Chart(ss, {
      type: 'line',
      data: {
        labels: ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'],
        datasets: [{
          data: [78, 80, 82, 84, 85, 87],
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.05)',
          tension: 0.3,
          fill: true,
          pointBackgroundColor: '#8b5cf6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: chartScales
      }
    });
  }

  // Safety Compliance radar
  const cc = document.getElementById('compliance-radar-chart');
  if (cc) {
    new Chart(cc, {
      type: 'radar',
      data: {
        labels: ['License Status', 'Safety Score', 'Medical Logs', 'Training', 'Clean Record'],
        datasets: [{
          label: 'Fleet Average',
          data: [82, 87, 90, 78, 85],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          pointBackgroundColor: '#2563eb'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  }

  // Expense breakdown donut
  const ec = document.getElementById('expense-chart');
  if (ec) {
    new Chart(ec, {
      type: 'doughnut',
      data: {
        labels: ['Fuel', 'Maintenance', 'Driver Wages', 'Insurance', 'Tolls'],
        datasets: [{
          data: [42840, 18320, 12480, 3200, 1700],
          backgroundColor: ['#ef4444', '#f59e0b', '#2563eb', '#8b5cf6', '#22c55e'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { font: fontOptions } } },
        cutout: '72%'
      }
    });
  }

  // Revenue vs Expense Trend line
  const pc = document.getElementById('profit-chart');
  if (pc) {
    new Chart(pc, {
      type: 'line',
      data: {
        labels: ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'],
        datasets: [
          {
            label: 'Revenue',
            data: [118000, 124000, 129000, 135000, 138000, 142300],
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.03)',
            tension: 0.3,
            fill: true
          },
          {
            label: 'Expenses',
            data: [82000, 79000, 80500, 77000, 79000, 78540],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.03)',
            tension: 0.3,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: chartScales
      }
    });
  }

  // Fuel Cost by Vehicle Type (Finance dashboard)
  const fc = document.getElementById('fuel-cost-chart');
  if (fc) {
    new Chart(fc, {
      type: 'bar',
      data: {
        labels: ['Trucks', 'Trailers', 'Vans', 'Tankers', 'Buses'],
        datasets: [{
          data: [18400, 12800, 6200, 4100, 1340],
          backgroundColor: '#ef4444',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: chartScales
      }
    });
  }
}
