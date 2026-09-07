/**
 * CareBridge Hospital Assistant - Unified Frontend Application Logic
 * Vanilla JavaScript (ES6+), Relative API Endpoints, Accessible UI
 */

const API_BASE = '/api';

// ==========================================================================
// Authentication & Session Storage
// ==========================================================================
const Auth = {
  getToken() {
    return localStorage.getItem('carebridge_token');
  },
  getUser() {
    try {
      const u = localStorage.getItem('carebridge_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },
  setSession(token, user) {
    localStorage.setItem('carebridge_token', token);
    localStorage.setItem('carebridge_user', JSON.stringify(user));
    this.updateNavbar();
  },
  clearSession() {
    localStorage.removeItem('carebridge_token');
    localStorage.removeItem('carebridge_user');
    this.updateNavbar();
  },
  isLoggedIn() {
    return !!this.getToken();
  },
  hasRole(role) {
    const u = this.getUser();
    return u && u.role === role;
  },
  logout() {
    this.clearSession();
    showToast('You have been logged out.', 'info');
    setTimeout(() => {
      window.location.href = '/login.html';
    }, 500);
  },
  updateNavbar() {
    const user = this.getUser();
    const navActions = document.getElementById('navbar-actions');
    const adminLink = document.getElementById('nav-admin-link');
    const dashboardLink = document.getElementById('nav-dashboard-link');

    if (adminLink) {
      adminLink.style.display = (user && (user.role === 'admin' || user.role === 'staff')) ? 'block' : 'none';
    }
    if (dashboardLink) {
      dashboardLink.style.display = user ? 'block' : 'none';
    }

    if (!navActions) return;

    if (user) {
      navActions.innerHTML = `
        <div class="user-pill" style="display:flex;align-items:center;gap:0.5rem;">
          <a href="/profile.html" class="btn btn-secondary btn-sm" title="My Profile">
            👤 <strong>${escapeHtml(user.name.split(' ')[0])}</strong>
            <span class="badge ${user.role === 'admin' ? 'badge-danger' : user.role === 'staff' ? 'badge-warning' : 'badge-info'}" style="font-size:0.65rem;margin-left:4px;">${user.role}</span>
          </a>
          <button class="btn btn-outline btn-sm" onclick="Auth.logout()" title="Sign Out">Logout</button>
        </div>
      `;
    } else {
      navActions.innerHTML = `
        <a href="/login.html" class="btn btn-secondary btn-sm">Login</a>
        <a href="/register.html" class="btn btn-primary btn-sm">Register</a>
      `;
    }
  }
};

// ==========================================================================
// Toast Notification System
// ==========================================================================
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = 'ℹ';
  if (type === 'success') icon = '✓';
  if (type === 'error') icon = '✕';
  if (type === 'emergency') icon = '⚠';
  if (type === 'warning') icon = '▲';

  toast.innerHTML = `
    <span style="font-weight:bold;font-size:1.1rem;line-height:1;">${icon}</span>
    <div style="flex:1;">${escapeHtml(message)}</div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ==========================================================================
// API Fetch Client
// ==========================================================================
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const token = Auth.getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, { ...options, headers });
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      if (res.status === 401) {
        Auth.clearSession();
        showToast('[AUTH] Session expired. Please login again.', 'error');
        if (!window.location.pathname.includes('login.html')) {
          setTimeout(() => window.location.href = '/login.html', 1200);
        }
      }
      const errorMsg = data.message || data.error || `[API] Request failed with status ${res.status}`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('[API] Unable to connect to server. Please check your connection.');
    }
    throw err;
  }
}

// Button loading state helper
function setButtonLoading(btn, isLoading, loadingText = 'Processing...') {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner" style="display:inline-block;width:12px;height:12px;border:2px solid #ffffff;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;margin-right:6px;"></span> ${loadingText}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalText || 'Submit';
    btn.disabled = false;
  }
}

// Utility: HTML Sanitizer
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Mobile Menu Toggle
function initMobileMenu() {
  const hamburger = document.getElementById('hamburger-btn');
  const navLinks = document.getElementById('nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('show');
    });
  }
}

// ==========================================================================
// Page Specific Initializers
// ==========================================================================

// 1. Landing Page
async function initLandingPage() {
  // Load preview departments
  try {
    const depts = await apiRequest('/departments');
    const container = document.getElementById('landing-departments-grid');
    if (container && depts) {
      container.innerHTML = depts.slice(0, 6).map(d => `
        <div class="card card-hover">
          <h3 style="font-size:1.15rem;margin-bottom:0.5rem;color:var(--primary);">${escapeHtml(d.name)}</h3>
          <p style="font-size:0.9rem;color:var(--text-muted);margin-bottom:1rem;line-height:1.5;">${escapeHtml(d.description)}</p>
          <div style="font-size:0.8rem;color:var(--text-light);margin-bottom:1rem;">
            📍 ${escapeHtml(d.location)} | 🕒 ${escapeHtml(d.opd_timing)}
          </div>
          <a href="/doctors.html?dept=${d.id}" class="btn btn-outline btn-sm">View Doctors (${d.doctor_count})</a>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading landing departments:', err);
  }

  // Load preview services
  try {
    const services = await apiRequest('/services');
    const container = document.getElementById('landing-services-grid');
    if (container && services) {
      container.innerHTML = services.slice(0, 6).map(s => `
        <div class="card card-hover">
          <div style="font-size:1.4rem;margin-bottom:0.5rem;">🏥</div>
          <h3 style="font-size:1.1rem;margin-bottom:0.4rem;">${escapeHtml(s.name)}</h3>
          <p style="font-size:0.88rem;color:var(--text-muted);margin-bottom:0.75rem;">${escapeHtml(s.description)}</p>
          <div style="font-size:0.8rem;color:var(--secondary);font-weight:600;">
            🕒 ${escapeHtml(s.timing)} • 📍 ${escapeHtml(s.location)}
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading landing services:', err);
  }
}

// 2. Chatbot Page
function initChatbotPage() {
  const chatMessages = document.getElementById('chat-messages');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const quickChips = document.getElementById('quick-chips');
  const newChatBtn = document.getElementById('new-chat-btn');
  const clearChatBtn = document.getElementById('clear-chat-btn');
  const sessionsList = document.getElementById('chat-sessions-list');

  let currentSessionId = localStorage.getItem('carebridge_active_session') || null;

  // Append a bubble to chat
  function appendMessage(sender, text, isEmergency = false, meta = null) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender} ${isEmergency ? 'emergency' : ''}`;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let confidenceTag = '';
    if (sender === 'bot' && meta && meta.intent) {
      const confPercent = Math.round((meta.confidence || 0) * 100);
      confidenceTag = `<span class="badge badge-neutral" style="font-size:0.65rem;">${escapeHtml(meta.intent)} (${confPercent}%)</span>`;
    }

    bubble.innerHTML = `
      <div class="bubble-content" ${sender === 'bot' ? 'aria-live="polite"' : ''}>${escapeHtml(text)}</div>
      <div class="bubble-meta">
        <span>${timeStr}</span>
        ${confidenceTag}
      </div>
    `;

    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Typing indicator
  function showTyping() {
    const id = 'typing-indicator';
    if (document.getElementById(id)) return;
    const typing = document.createElement('div');
    typing.id = id;
    typing.className = 'typing-indicator';
    typing.innerHTML = `
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    `;
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
  }

  // Send message
  async function sendMessage(text) {
    const msg = (text || (chatInput ? chatInput.value : '')).trim();
    if (!msg) return;

    if (chatInput) chatInput.value = '';
    appendMessage('user', msg);
    showTyping();

    if (sendBtn) sendBtn.disabled = true;

    try {
      const res = await apiRequest('/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: msg,
          session_id: currentSessionId
        })
      });

      hideTyping();
      if (res.session_id) {
        currentSessionId = res.session_id;
        localStorage.setItem('carebridge_active_session', currentSessionId);
      }

      appendMessage('bot', res.response, res.safety_flag, {
        intent: res.intent,
        confidence: res.confidence
      });

      if (res.safety_flag) {
        showToast('⚠ Medical emergency guidance detected.', 'emergency', 6000);
      }
    } catch (err) {
      hideTyping();
      appendMessage('bot', `[SYSTEM ERROR] ${err.message}`);
      showToast(err.message, 'error');
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      if (chatInput) chatInput.focus();
    }
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', () => sendMessage());
  }

  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // Quick Chips
  if (quickChips) {
    quickChips.addEventListener('click', (e) => {
      const chip = e.target.closest('.chip');
      if (chip) {
        const query = chip.dataset.query || chip.textContent.trim();
        sendMessage(query);
      }
    });
  }

  // New Chat
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      currentSessionId = null;
      localStorage.removeItem('carebridge_active_session');
      chatMessages.innerHTML = '';
      appendMessage('bot', "Hello! I'm your CareBridge Hospital Assistant. How can I help you today?");
      showToast('Started a new conversation session.', 'info');
    });
  }

  // Clear Chat
  if (clearChatBtn) {
    clearChatBtn.addEventListener('click', () => {
      chatMessages.innerHTML = '';
      appendMessage('bot', "Chat cleared. Ask about doctors, appointments, departments, or hospital timings!");
    });
  }

  // Load Past Chat History if authenticated
  if (Auth.isLoggedIn() && sessionsList) {
    apiRequest('/chat/history').then(sessions => {
      if (sessions && sessions.length) {
        sessionsList.innerHTML = sessions.map(s => `
          <div class="chat-session-item" data-session-id="${s.id}">
            <div style="font-weight:600;font-size:0.85rem;">Session ${s.id.substring(0, 8)}...</div>
            <div style="font-size:0.75rem;color:var(--text-muted);">${new Date(s.updated_at).toLocaleDateString()} (${s.message_count} msgs)</div>
          </div>
        `).join('');

        sessionsList.addEventListener('click', (e) => {
          const item = e.target.closest('.chat-session-item');
          if (item) {
            const sid = item.dataset.sessionId;
            loadSessionMessages(sid);
          }
        });
      } else {
        sessionsList.innerHTML = `<div style="padding:1rem;color:var(--text-light);font-size:0.85rem;text-align:center;">No previous sessions</div>`;
      }
    }).catch(console.error);
  }

  async function loadSessionMessages(sid) {
    try {
      const data = await apiRequest(`/chat/history?session_id=${sid}`);
      if (data && data.messages) {
        currentSessionId = sid;
        localStorage.setItem('carebridge_active_session', sid);
        chatMessages.innerHTML = '';
        data.messages.forEach(m => {
          appendMessage(m.sender, m.message, m.safety_flag, {
            intent: m.intent,
            confidence: m.confidence
          });
        });
        showToast(`Loaded conversation history.`, 'info');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  }
}

// 3. Doctors Page
async function initDoctorsPage() {
  const doctorsGrid = document.getElementById('doctors-grid');
  const deptFilter = document.getElementById('doctor-dept-filter');
  const searchInput = document.getElementById('doctor-search');
  const bookingModal = document.getElementById('booking-modal');

  let allDoctors = [];

  // Load departments into dropdown
  try {
    const depts = await apiRequest('/departments');
    if (deptFilter && depts) {
      depts.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = d.name;
        deptFilter.appendChild(opt);
      });

      // Check URL search params for initial filter
      const urlParams = new URLSearchParams(window.location.search);
      const initialDept = urlParams.get('dept');
      if (initialDept) {
        deptFilter.value = initialDept;
      }
    }
  } catch (err) {
    console.error(err);
  }

  // Load doctors
  async function fetchDoctors() {
    if (!doctorsGrid) return;
    doctorsGrid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted);">Loading doctors directory...</div>`;

    const deptId = deptFilter ? deptFilter.value : '';
    const search = searchInput ? searchInput.value.trim() : '';

    let url = '/doctors';
    const params = [];
    if (deptId) params.push(`department_id=${deptId}`);
    if (search) params.push(`search=${encodeURIComponent(search)}`);
    if (params.length) url += `?${params.join('&')}`;

    try {
      allDoctors = await apiRequest(url);
      renderDoctors(allDoctors);
    } catch (err) {
      doctorsGrid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--danger);">${err.message}</div>`;
    }
  }

  function renderDoctors(doctors) {
    if (!doctors || doctors.length === 0) {
      doctorsGrid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:4rem;background:#ffffff;border-radius:var(--radius-lg);border:1px solid var(--border);">
          <div style="font-size:2.5rem;margin-bottom:1rem;">🩺</div>
          <h3>No doctors found</h3>
          <p style="color:var(--text-muted);margin-top:0.5rem;">Try adjusting your department filter or search keywords.</p>
        </div>
      `;
      return;
    }

    doctorsGrid.innerHTML = doctors.map(doc => `
      <div class="card doctor-card card-hover">
        <div>
          <div class="doctor-avatar">${doc.name.replace('Dr. ', '').charAt(0)}</div>
          <h3 class="doctor-name">${escapeHtml(doc.name)}</h3>
          <div class="doctor-spec">${escapeHtml(doc.department_name)} • ${escapeHtml(doc.specialization)}</div>
          <div class="doctor-meta">
            <div class="doctor-meta-item">🎓 <span>${escapeHtml(doc.qualification)} (${escapeHtml(doc.experience)})</span></div>
            <div class="doctor-meta-item">🕒 <span>${escapeHtml(doc.available_days)} (${escapeHtml(doc.start_time)} - ${escapeHtml(doc.end_time)})</span></div>
            <div class="doctor-meta-item">📍 <span>${escapeHtml(doc.room_number)}</span></div>
          </div>
        </div>
        <div class="doctor-card-footer">
          <div class="doctor-fee">$${doc.consultation_fee.toFixed(2)} <span>/ consult</span></div>
          <div style="display:flex;gap:0.5rem;">
            <a href="/doctor-details.html?id=${doc.id}" class="btn btn-secondary btn-sm">Profile</a>
            <button class="btn btn-primary btn-sm" onclick="openBookingModal(${doc.id}, '${escapeHtml(doc.name)}', '${escapeHtml(doc.department_name)}')">Book</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  if (deptFilter) deptFilter.addEventListener('change', fetchDoctors);
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchDoctors, 300);
    });
  }

  fetchDoctors();
}

// Booking Modal Functionality (Accessible across pages)
window.openBookingModal = async function(doctorId, doctorName, departmentName) {
  if (!Auth.isLoggedIn()) {
    showToast('Please login to book an appointment.', 'warning');
    setTimeout(() => {
      window.location.href = `/login.html?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
    }, 1000);
    return;
  }

  let modal = document.getElementById('booking-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'booking-modal';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  // Pre-fill tomorrow as default date
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];

  modal.innerHTML = `
    <div class="modal-card">
      <div class="modal-header">
        <h3 style="font-size:1.2rem;">Book Appointment</h3>
        <button class="btn btn-secondary btn-sm" onclick="closeBookingModal()">✕</button>
      </div>
      <form id="booking-modal-form" onsubmit="submitAppointmentBooking(event, ${doctorId})">
        <div class="modal-body">
          <div style="margin-bottom:1.25rem;padding:0.85rem;background:var(--primary-light);border-radius:var(--radius-md);color:var(--text-main);">
            <strong>${escapeHtml(doctorName)}</strong>
            <div style="font-size:0.85rem;color:var(--primary);">${escapeHtml(departmentName)}</div>
          </div>

          <div class="form-group">
            <label class="form-label" for="booking-date">Consultation Date</label>
            <input type="date" id="booking-date" class="form-control" value="${tomorrowStr}" min="${new Date().toISOString().split('T')[0]}" required onchange="loadDoctorAvailableSlots(${doctorId})">
          </div>

          <div class="form-group">
            <label class="form-label">Available Time Slots</label>
            <div id="booking-slots-container" style="display:flex;flex-wrap:wrap;gap:0.5rem;max-height:160px;overflow-y:auto;padding:0.5rem 0;">
              <span style="font-size:0.85rem;color:var(--text-muted);">Loading available slots...</span>
            </div>
            <input type="hidden" id="booking-time" required>
          </div>

          <div class="form-group">
            <label class="form-label" for="booking-reason">Reason for Visit / Health Symptoms</label>
            <textarea id="booking-reason" class="form-control" rows="2" placeholder="e.g. Follow-up consultation, chest tightness, routine checkup"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" onclick="closeBookingModal()">Cancel</button>
          <button type="submit" id="btn-submit-booking" class="btn btn-primary">Confirm Appointment</button>
        </div>
      </form>
    </div>
  `;

  modal.classList.add('active');
  loadDoctorAvailableSlots(doctorId);
};

window.closeBookingModal = function() {
  const modal = document.getElementById('booking-modal');
  if (modal) modal.classList.remove('active');
};

window.loadDoctorAvailableSlots = async function(doctorId) {
  const dateInput = document.getElementById('booking-date');
  const container = document.getElementById('booking-slots-container');
  const timeHidden = document.getElementById('booking-time');
  if (!dateInput || !container) return;

  const targetDate = dateInput.value;
  if (!targetDate) return;

  container.innerHTML = `<span style="font-size:0.85rem;color:var(--text-muted);">Checking doctor schedule...</span>`;

  try {
    const res = await apiRequest(`/doctors/${doctorId}/availability?date=${targetDate}`);
    if (!res.is_available_day) {
      container.innerHTML = `<span style="font-size:0.85rem;color:var(--danger);">${escapeHtml(res.message)}</span>`;
      if (timeHidden) timeHidden.value = '';
      return;
    }

    if (!res.available_slots || res.available_slots.length === 0) {
      container.innerHTML = `<span style="font-size:0.85rem;color:var(--warning);">All slots are fully booked for this date. Please pick another date.</span>`;
      if (timeHidden) timeHidden.value = '';
      return;
    }

    container.innerHTML = res.available_slots.map(slot => `
      <button type="button" class="chip slot-chip" onclick="selectSlot(this, '${slot}')">${slot}</button>
    `).join('');

    // Auto select first slot
    const firstChip = container.querySelector('.slot-chip');
    if (firstChip) selectSlot(firstChip, res.available_slots[0]);

  } catch (err) {
    container.innerHTML = `<span style="font-size:0.85rem;color:var(--danger);">${err.message}</span>`;
  }
};

window.selectSlot = function(el, timeSlot) {
  document.querySelectorAll('.slot-chip').forEach(c => {
    c.style.background = 'var(--bg-subtle)';
    c.style.color = 'var(--text-main)';
    c.style.borderColor = 'var(--border)';
  });
  el.style.background = 'var(--primary)';
  el.style.color = '#ffffff';
  el.style.borderColor = 'var(--primary)';

  const timeHidden = document.getElementById('booking-time');
  if (timeHidden) timeHidden.value = timeSlot;
};

window.submitAppointmentBooking = async function(e, doctorId) {
  e.preventDefault();
  const dateInput = document.getElementById('booking-date');
  const timeInput = document.getElementById('booking-time');
  const reasonInput = document.getElementById('booking-reason');
  const submitBtn = document.getElementById('btn-submit-booking');

  if (!timeInput || !timeInput.value) {
    showToast('Please select a consultation time slot.', 'warning');
    return;
  }

  setButtonLoading(submitBtn, true, 'Booking Slot...');

  try {
    const res = await apiRequest('/appointments', {
      method: 'POST',
      body: JSON.stringify({
        doctor_id: doctorId,
        appointment_date: dateInput.value,
        appointment_time: timeInput.value,
        reason: reasonInput.value
      })
    });

    closeBookingModal();
    showToast(`✓ Appointment confirmed! Reference ID: ${res.appointment.id}`, 'success', 5000);

    // If on appointments page, refresh list
    if (window.location.pathname.includes('appointments.html')) {
      loadAppointments();
    }
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error', 5000);
  } finally {
    setButtonLoading(submitBtn, false);
  }
};

// 4. Doctor Details Page
async function initDoctorDetailsPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const docId = urlParams.get('id');
  const container = document.getElementById('doctor-details-container');

  if (!docId || !container) {
    if (container) container.innerHTML = `<div class="card" style="text-align:center;padding:3rem;">No doctor selected. <a href="/doctors.html">Back to directory</a></div>`;
    return;
  }

  try {
    const doc = await apiRequest(`/doctors/${docId}`);
    document.title = `${doc.name} - CareBridge Hospital`;

    container.innerHTML = `
      <div class="card" style="max-width:800px;margin:0 auto;">
        <div style="display:flex;align-items:flex-start;gap:2rem;flex-wrap:wrap;margin-bottom:2rem;">
          <div class="doctor-avatar" style="width:100px;height:100px;font-size:2.5rem;">
            ${doc.name.replace('Dr. ', '').charAt(0)}
          </div>
          <div style="flex:1;">
            <h1 style="font-size:2rem;margin-bottom:0.25rem;">${escapeHtml(doc.name)}</h1>
            <div style="color:var(--primary);font-weight:700;font-size:1.1rem;margin-bottom:0.75rem;">
              ${escapeHtml(doc.department_name)} • ${escapeHtml(doc.specialization)}
            </div>
            <div style="display:flex;gap:0.75rem;flex-wrap:wrap;">
              <span class="badge badge-success">Active Specialist</span>
              <span class="badge badge-info">${escapeHtml(doc.experience)} Clinical Experience</span>
            </div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:1.5rem;padding:1.5rem;background:var(--bg-subtle);border-radius:var(--radius-lg);margin-bottom:2rem;">
          <div>
            <div style="font-size:0.8rem;color:var(--text-muted);font-weight:600;">QUALIFICATIONS</div>
            <div style="font-weight:700;margin-top:2px;">${escapeHtml(doc.qualification)}</div>
          </div>
          <div>
            <div style="font-size:0.8rem;color:var(--text-muted);font-weight:600;">CONSULTATION FEE</div>
            <div style="font-weight:700;font-size:1.2rem;color:var(--primary);margin-top:2px;">$${doc.consultation_fee.toFixed(2)}</div>
          </div>
          <div>
            <div style="font-size:0.8rem;color:var(--text-muted);font-weight:600;">CONSULTING HOURS</div>
            <div style="font-weight:700;margin-top:2px;">${escapeHtml(doc.start_time)} - ${escapeHtml(doc.end_time)}</div>
          </div>
          <div>
            <div style="font-size:0.8rem;color:var(--text-muted);font-weight:600;">CLINIC / ROOM</div>
            <div style="font-weight:700;margin-top:2px;">${escapeHtml(doc.room_number)}</div>
          </div>
        </div>

        <div style="margin-bottom:2rem;">
          <h3 style="margin-bottom:0.75rem;">Available Consulting Days</h3>
          <p style="color:var(--text-muted);">${escapeHtml(doc.available_days)}</p>
        </div>

        <div style="display:flex;gap:1rem;justify-content:flex-end;">
          <a href="/doctors.html" class="btn btn-secondary">Back to Doctors</a>
          <button class="btn btn-primary btn-lg" onclick="openBookingModal(${doc.id}, '${escapeHtml(doc.name)}', '${escapeHtml(doc.department_name)}')">Book Appointment</button>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="card" style="text-align:center;color:var(--danger);">${err.message}</div>`;
  }
}

// 5. Departments Page
async function initDepartmentsPage() {
  const container = document.getElementById('departments-grid');
  if (!container) return;

  try {
    const depts = await apiRequest('/departments');
    container.innerHTML = depts.map(d => `
      <div class="card card-hover">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
          <h3 style="font-size:1.25rem;color:var(--primary);">${escapeHtml(d.name)}</h3>
          <span class="badge badge-info">${d.doctor_count} Doctors</span>
        </div>
        <p style="color:var(--text-muted);font-size:0.92rem;margin-bottom:1.25rem;line-height:1.6;">${escapeHtml(d.description)}</p>
        <div style="border-top:1px solid var(--border);padding-top:1rem;margin-bottom:1.25rem;font-size:0.85rem;color:var(--text-muted);display:flex;flex-direction:column;gap:0.4rem;">
          <div>📍 <strong>Location:</strong> ${escapeHtml(d.location)}</div>
          <div>🕒 <strong>OPD Timings:</strong> ${escapeHtml(d.opd_timing)}</div>
        </div>
        <a href="/doctors.html?dept=${d.id}" class="btn btn-outline" style="width:100%;">View Department Doctors</a>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--danger);">${err.message}</div>`;
  }
}

// 6. Appointments Page
async function initAppointmentsPage() {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/login.html?redirect=/appointments.html';
    return;
  }
  loadAppointments();
}

window.loadAppointments = async function(statusFilter = null) {
  const container = document.getElementById('appointments-list');
  if (!container) return;

  container.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-muted);">Loading your appointments...</div>`;

  let url = '/appointments';
  if (statusFilter && statusFilter !== 'all') {
    url += `?status=${statusFilter}`;
  }

  try {
    const apts = await apiRequest(url);
    const user = Auth.getUser();
    const isStaffOrAdmin = user && (user.role === 'staff' || user.role === 'admin');

    if (!apts || apts.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:4rem;">
          <div style="font-size:3rem;margin-bottom:1rem;">📅</div>
          <h3>No appointments found</h3>
          <p style="color:var(--text-muted);margin:0.5rem 0 1.5rem;">You do not have any appointments under this view.</p>
          <a href="/doctors.html" class="btn btn-primary">Book an Appointment</a>
        </div>
      `;
      return;
    }

    container.innerHTML = apts.map(apt => {
      let badgeClass = 'badge-info';
      if (apt.status === 'confirmed') badgeClass = 'badge-success';
      if (apt.status === 'cancelled') badgeClass = 'badge-danger';
      if (apt.status === 'completed') badgeClass = 'badge-neutral';

      const canCancel = apt.status === 'confirmed' || apt.status === 'pending';

      return `
        <div class="card" style="margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1.5rem;">
          <div>
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.4rem;">
              <span class="badge ${badgeClass}">${apt.status.toUpperCase()}</span>
              <span style="font-weight:700;font-size:0.9rem;color:var(--text-muted);">${escapeHtml(apt.id)}</span>
            </div>
            <h3 style="font-size:1.2rem;margin-bottom:0.25rem;">${escapeHtml(apt.doctor_name)}</h3>
            <div style="font-size:0.9rem;color:var(--primary);font-weight:600;margin-bottom:0.5rem;">
              ${escapeHtml(apt.department_name)} • ${escapeHtml(apt.room_number)}
            </div>
            <div style="font-size:0.85rem;color:var(--text-muted);">
              📅 <strong>${escapeHtml(apt.appointment_date)}</strong> at <strong>${escapeHtml(apt.appointment_time)}</strong>
              ${isStaffOrAdmin ? ` | 👤 Patient: <strong>${escapeHtml(apt.patient_name)}</strong> (${escapeHtml(apt.patient_phone || apt.patient_email)})` : ''}
            </div>
            <div style="font-size:0.85rem;color:var(--text-light);margin-top:0.35rem;">
              Reason: ${escapeHtml(apt.reason)}
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:0.75rem;">
            ${isStaffOrAdmin ? `
              <select class="form-control" style="width:auto;padding:0.4rem 0.75rem;font-size:0.85rem;" onchange="updateAptStatus('${apt.id}', this.value)">
                <option value="pending" ${apt.status === 'pending' ? 'selected' : ''}>Pending</option>
                <option value="confirmed" ${apt.status === 'confirmed' ? 'selected' : ''}>Confirmed</option>
                <option value="completed" ${apt.status === 'completed' ? 'selected' : ''}>Completed</option>
                <option value="cancelled" ${apt.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
              </select>
            ` : ''}

            ${canCancel ? `
              <button class="btn btn-danger btn-sm" onclick="cancelAppointment('${apt.id}')">Cancel</button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div class="card" style="text-align:center;color:var(--danger);">${err.message}</div>`;
  }
};

window.cancelAppointment = async function(aptId) {
  if (!confirm(`Are you sure you want to cancel appointment ${aptId}?`)) return;

  try {
    await apiRequest(`/appointments/${aptId}`, { method: 'DELETE' });
    showToast(`Appointment ${aptId} cancelled.`, 'success');
    loadAppointments();
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error');
  }
};

window.updateAptStatus = async function(aptId, newStatus) {
  try {
    await apiRequest(`/appointments/${aptId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status: newStatus })
    });
    showToast(`Status updated to ${newStatus}.`, 'success');
    loadAppointments();
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error');
  }
};

// 7. Patient Dashboard
async function initDashboardPage() {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/login.html?redirect=/dashboard.html';
    return;
  }

  const user = Auth.getUser();
  const welcomeEl = document.getElementById('dashboard-welcome-name');
  if (welcomeEl && user) {
    welcomeEl.textContent = user.name;
  }

  // Load upcoming appointment & stats
  try {
    const apts = await apiRequest('/appointments');
    const upcomingContainer = document.getElementById('dashboard-upcoming-apt');
    const totalAptsEl = document.getElementById('dashboard-total-apts');

    if (totalAptsEl) totalAptsEl.textContent = apts ? apts.length : '0';

    if (upcomingContainer) {
      const activeApts = apts ? apts.filter(a => a.status === 'confirmed' || a.status === 'pending') : [];
      if (activeApts.length > 0) {
        const nextApt = activeApts[0];
        upcomingContainer.innerHTML = `
          <div style="background:var(--primary-light);padding:1.25rem;border-radius:var(--radius-lg);border-left:4px solid var(--primary);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
              <span class="badge badge-success">${nextApt.status.toUpperCase()}</span>
              <span style="font-size:0.8rem;color:var(--primary);font-weight:700;">${nextApt.id}</span>
            </div>
            <h4 style="font-size:1.2rem;margin-bottom:0.25rem;">${escapeHtml(nextApt.doctor_name)}</h4>
            <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:0.75rem;">${escapeHtml(nextApt.department_name)} • ${escapeHtml(nextApt.room_number)}</p>
            <div style="font-size:0.85rem;color:var(--text-main);font-weight:600;">
              📅 ${escapeHtml(nextApt.appointment_date)} at ${escapeHtml(nextApt.appointment_time)}
            </div>
            <div style="margin-top:1rem;">
              <a href="/appointments.html" class="btn btn-primary btn-sm">Manage Appointments</a>
            </div>
          </div>
        `;
      } else {
        upcomingContainer.innerHTML = `
          <div style="text-align:center;padding:2rem;color:var(--text-muted);">
            <p>No upcoming appointments scheduled.</p>
            <a href="/doctors.html" class="btn btn-outline btn-sm" style="margin-top:0.75rem;">Book a Consultation</a>
          </div>
        `;
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// 8. Profile Page
async function initProfilePage() {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/login.html?redirect=/profile.html';
    return;
  }

  try {
    const res = await apiRequest('/auth/me');
    const u = res.user;

    const nameInput = document.getElementById('profile-name');
    const emailInput = document.getElementById('profile-email');
    const phoneInput = document.getElementById('profile-phone');
    const roleInput = document.getElementById('profile-role');

    if (nameInput) nameInput.value = u.name;
    if (emailInput) emailInput.value = u.email;
    if (phoneInput) phoneInput.value = u.phone || '';
    if (roleInput) roleInput.value = u.role.toUpperCase();

    const form = document.getElementById('profile-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-save-profile');
        setButtonLoading(submitBtn, true, 'Saving...');

        try {
          const updated = await apiRequest('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify({
              name: nameInput.value,
              phone: phoneInput.value
            })
          });
          Auth.setSession(Auth.getToken(), updated.user);
          showToast('Profile updated successfully.', 'success');
        } catch (err) {
          showToast(`✕ ${err.message}`, 'error');
        } finally {
          setButtonLoading(submitBtn, false);
        }
      });
    }
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error');
  }
}

// 9. FAQ Page
async function initFaqPage() {
  const accordionContainer = document.getElementById('faq-accordion');
  const searchInput = document.getElementById('faq-search');
  const categoryFilters = document.getElementById('faq-category-filters');

  let currentCategory = 'all';

  async function fetchFaqs() {
    if (!accordionContainer) return;
    const query = searchInput ? searchInput.value.trim() : '';

    let url = '/faqs';
    const params = [];
    if (currentCategory && currentCategory !== 'all') params.push(`category=${encodeURIComponent(currentCategory)}`);
    if (query) params.push(`search=${encodeURIComponent(query)}`);
    if (params.length) url += `?${params.join('&')}`;

    try {
      const faqs = await apiRequest(url);
      if (!faqs || faqs.length === 0) {
        accordionContainer.innerHTML = `<div class="card" style="text-align:center;padding:3rem;color:var(--text-muted);">No matching FAQs found.</div>`;
        return;
      }

      accordionContainer.innerHTML = faqs.map(f => `
        <div class="faq-item">
          <button class="faq-question" onclick="toggleFaq(this)">
            <span>${escapeHtml(f.question)}</span>
            <span class="faq-icon">▾</span>
          </button>
          <div class="faq-answer">
            <div class="faq-answer-inner">${escapeHtml(f.answer)}</div>
          </div>
        </div>
      `).join('');
    } catch (err) {
      accordionContainer.innerHTML = `<div style="color:var(--danger);">${err.message}</div>`;
    }
  }

  window.toggleFaq = function(btn) {
    const item = btn.parentElement;
    const answer = item.querySelector('.faq-answer');
    const isOpen = item.classList.contains('active');

    // Close others
    document.querySelectorAll('.faq-item').forEach(i => {
      i.classList.remove('active');
      const a = i.querySelector('.faq-answer');
      if (a) a.style.maxHeight = null;
    });

    if (!isOpen) {
      item.classList.add('active');
      answer.style.maxHeight = answer.scrollHeight + 'px';
    }
  };

  if (categoryFilters) {
    categoryFilters.addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (btn) {
        categoryFilters.querySelectorAll('button').forEach(b => b.classList.remove('btn-primary'));
        categoryFilters.querySelectorAll('button').forEach(b => b.classList.add('btn-secondary'));
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-primary');
        currentCategory = btn.dataset.category || 'all';
        fetchFaqs();
      }
    });
  }

  if (searchInput) {
    let timer;
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(fetchFaqs, 300);
    });
  }

  fetchFaqs();
}

// 10. Admin Page (Protected & Chart.js Visualizations)
async function initAdminPage() {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/login.html?redirect=/admin.html';
    return;
  }
  const user = Auth.getUser();
  if (user.role !== 'admin' && user.role !== 'staff') {
    showToast('Forbidden. Administrator privileges required.', 'error');
    setTimeout(() => window.location.href = '/dashboard.html', 1500);
    return;
  }

  // Load KPI metrics and Chart.js visualizations
  try {
    const data = await apiRequest('/admin/analytics');
    const m = data.metrics;

    document.getElementById('metric-patients').textContent = m.total_patients;
    document.getElementById('metric-doctors').textContent = m.total_doctors;
    document.getElementById('metric-appointments-today').textContent = m.appointments_today;
    document.getElementById('metric-departments').textContent = m.total_departments;
    document.getElementById('metric-chat-sessions').textContent = m.chat_sessions;
    document.getElementById('metric-emergency-flags').textContent = m.emergency_flags;
    document.getElementById('metric-avg-confidence').textContent = `${Math.round(m.average_confidence * 100)}%`;

    // Render Charts if Chart is loaded
    if (typeof Chart !== 'undefined') {
      renderAdminCharts(data.charts);
    }
  } catch (err) {
    showToast(`Failed to load analytics: ${err.message}`, 'error');
  }

  // Load Management Tables
  loadAdminDoctors();
  loadAdminDepartments();
  loadAdminFaqs();
}

function renderAdminCharts(chartData) {
  // Chart 1: Appointments Over Time
  const timelineCtx = document.getElementById('chart-appointments-timeline');
  if (timelineCtx && chartData.appointments_timeline) {
    new Chart(timelineCtx, {
      type: 'line',
      data: {
        labels: Object.keys(chartData.appointments_timeline),
        datasets: [{
          label: 'Appointments',
          data: Object.values(chartData.appointments_timeline),
          borderColor: '#0284c7',
          backgroundColor: 'rgba(2, 132, 199, 0.1)',
          tension: 0.3,
          fill: true
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  // Chart 2: Appointments by Department
  const deptCtx = document.getElementById('chart-appointments-dept');
  if (deptCtx && chartData.department_appointments) {
    new Chart(deptCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(chartData.department_appointments),
        datasets: [{
          label: 'Appointments',
          data: Object.values(chartData.department_appointments),
          backgroundColor: '#0f766e'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  // Chart 3: Chatbot Intent Distribution
  const intentCtx = document.getElementById('chart-intent-dist');
  if (intentCtx && chartData.intent_distribution) {
    new Chart(intentCtx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(chartData.intent_distribution),
        datasets: [{
          data: Object.values(chartData.intent_distribution),
          backgroundColor: ['#0284c7', '#0f766e', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#64748b']
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }
}

// Admin Doctors CRUD Table
window.loadAdminDoctors = async function() {
  const tbody = document.getElementById('admin-doctors-tbody');
  if (!tbody) return;

  try {
    const docs = await apiRequest('/doctors');
    tbody.innerHTML = docs.map(d => `
      <tr>
        <td><strong>${escapeHtml(d.name)}</strong></td>
        <td>${escapeHtml(d.department_name)}</td>
        <td>${escapeHtml(d.specialization)}</td>
        <td>$${d.consultation_fee.toFixed(2)}</td>
        <td><span class="badge ${d.status === 'active' ? 'badge-success' : 'badge-warning'}">${d.status}</span></td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="editDoctor(${d.id})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="deleteDoctor(${d.id})">Delete</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--danger);text-align:center;">${err.message}</td></tr>`;
  }
};

window.deleteDoctor = async function(id) {
  if (!confirm('Are you sure you want to delete this doctor?')) return;
  try {
    await apiRequest(`/admin/doctors/${id}`, { method: 'DELETE' });
    showToast('Doctor deleted successfully.', 'success');
    loadAdminDoctors();
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error');
  }
};

// Admin Departments CRUD Table
window.loadAdminDepartments = async function() {
  const tbody = document.getElementById('admin-depts-tbody');
  if (!tbody) return;

  try {
    const depts = await apiRequest('/departments');
    tbody.innerHTML = depts.map(d => `
      <tr>
        <td><strong>${escapeHtml(d.name)}</strong></td>
        <td>${escapeHtml(d.location)}</td>
        <td>${escapeHtml(d.opd_timing)}</td>
        <td>${d.doctor_count}</td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="deleteDepartment(${d.id})">Delete</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--danger);text-align:center;">${err.message}</td></tr>`;
  }
};

window.deleteDepartment = async function(id) {
  if (!confirm('Are you sure you want to delete this department?')) return;
  try {
    await apiRequest(`/admin/departments/${id}`, { method: 'DELETE' });
    showToast('Department deleted successfully.', 'success');
    loadAdminDepartments();
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error');
  }
};

// Admin FAQs CRUD Table
window.loadAdminFaqs = async function() {
  const tbody = document.getElementById('admin-faqs-tbody');
  if (!tbody) return;

  try {
    const faqs = await apiRequest('/faqs');
    tbody.innerHTML = faqs.map(f => `
      <tr>
        <td><span class="badge badge-info">${escapeHtml(f.category)}</span></td>
        <td><strong>${escapeHtml(f.question)}</strong></td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="deleteFaq(${f.id})">Delete</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="3" style="color:var(--danger);text-align:center;">${err.message}</td></tr>`;
  }
};

window.deleteFaq = async function(id) {
  if (!confirm('Are you sure you want to delete this FAQ?')) return;
  try {
    await apiRequest(`/admin/faqs/${id}`, { method: 'DELETE' });
    showToast('FAQ deleted successfully.', 'success');
    loadAdminFaqs();
  } catch (err) {
    showToast(`✕ ${err.message}`, 'error');
  }
};

// Global Bootstrapper
document.addEventListener('DOMContentLoaded', () => {
  Auth.updateNavbar();
  initMobileMenu();

  const path = window.location.pathname;

  if (path === '/' || path.endsWith('index.html') || path === '') {
    initLandingPage();
  } else if (path.includes('chatbot.html')) {
    initChatbotPage();
  } else if (path.includes('doctors.html')) {
    initDoctorsPage();
  } else if (path.includes('doctor-details.html')) {
    initDoctorDetailsPage();
  } else if (path.includes('departments.html')) {
    initDepartmentsPage();
  } else if (path.includes('appointments.html')) {
    initAppointmentsPage();
  } else if (path.includes('dashboard.html')) {
    initDashboardPage();
  } else if (path.includes('profile.html')) {
    initProfilePage();
  } else if (path.includes('faq.html')) {
    initFaqPage();
  } else if (path.includes('admin.html')) {
    initAdminPage();
  }
});
