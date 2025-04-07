<template>
  <!-- Loading State -->
  <div v-if="!loggedIn" class="loading-container">
    <div class="loader loader-large"></div>
    <h2>Loading Your Nurse Dashboard</h2>
    <p>Please wait while we retrieve your information...</p>
  </div>

  <!-- Main Dashboard -->
  <div v-else class="booking-container">
    <!-- Dashboard Header -->
    <header class="dashboard-header">
      <div class="user-welcome">
        <h1>Hello, {{ selectedNurse.name }}</h1>
        <p class="subtitle">Manage your patient appointments from one place</p>
      </div>
      <div class="header-stats">
        <div class="stat-card">
          <span class="stat-number">{{ bookings.length }}</span>
          <span class="stat-label">Total Appointments</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{ bookings.filter(b => b.fields.Status?.stringValue === 'Pending').length }}</span>
          <span class="stat-label">Pending</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{ bookings.filter(b => b.fields.Status?.stringValue === 'Completed').length }}</span>
          <span class="stat-label">Completed</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{ bookings.filter(b => b.fields.Status?.stringValue === 'Cancelled').length }}</span>
          <span class="stat-label">Cancelled</span>
        </div>
      </div>
    </header>

    <!-- Bookings Management Section -->
    <!-- Restructured View Bookings Section -->
    <section class="view-bookings">
      <div class="section-header">
        <div class="section-title">
          <h2>Your Assigned Appointments</h2>
          <span class="section-badge">{{ bookings.length }} Total</span>
        </div>
        <button class="btn-refresh" @click="getBookings" :disabled="isLoadingBookings">
      <span v-if="isLoadingBookings" class="btn-icon">
        <span class="spin-loader"></span>
      </span>
          <span v-else class="btn-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 2v6h-6"></path>
          <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
          <path d="M3 22v-6h6"></path>
          <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
        </svg>
      </span>
          <span>{{ isLoadingBookings ? 'Updating...' : 'Refresh' }}</span>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoadingBookings" class="loader-container">
        <div class="loader"></div>
        <p>Loading your appointments...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="bookings.length === 0" class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>You don't have any appointments yet</p>
        <p class="hint-text">When patients schedule appointments with you, they'll appear here</p>
      </div>

      <!-- Bookings Table -->
      <div v-else class="table-responsive">
        <!-- Table Actions (Filters & Search) -->
        <div class="table-actions">
          <div class="table-filter">
            <select v-model="statusFilter" class="filter-select">
              <option value="all">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div class="table-search">
            <div class="search-input-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input type="text" v-model="searchQuery" placeholder="Search patients, notes..." class="search-input">
            </div>
          </div>
        </div>

        <!-- Filtered Empty State -->
        <div v-if="filteredBookings.length === 0" class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <p>No appointments match your filters</p>
          <button class="btn-link" @click="resetFilters">Reset filters</button>
        </div>

        <!-- Table with Data -->
        <table v-else>
          <thead>
          <tr>
            <th>Patient</th>
            <th>Date & Time</th>
            <th>Status</th>
            <th>Notes</th>
            <th>Payment</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(booking, index) in filteredBookings" :key="index">
            <!-- Patient -->
            <td>
              <div class="patient-info" @click="viewPatientInfo(booking.fields.PID?.stringValue)">
                <div class="patient-avatar">{{ getPatientInitials(booking.fields.PID?.stringValue) }}</div>
                <div class="patient-details">
                  <p class="patient-name">{{ getPatientName(booking.fields.PID?.stringValue) }}</p>
                  <p class="booking-id">ID: {{ booking.fields.BID?.stringValue }}</p>
                </div>
              </div>
            </td>

            <!-- Schedule -->
            <td>
              <div class="booking-time">
                <div class="date">{{ formatDate(booking.fields.StartTime?.timestampValue) }}</div>
                <div class="time">
                  {{ formatTime(booking.fields.StartTime?.timestampValue) }} -
                  {{ formatTime(booking.fields.EndTime?.timestampValue) }}
                </div>
                <div class="duration">
                  {{ calculateDuration(booking.fields.StartTime?.timestampValue, booking.fields.EndTime?.timestampValue) }}
                </div>
              </div>
            </td>

            <!-- Status -->
            <td>
              <span :class="['status-badge', getStatusClass(booking.fields.Status?.stringValue)]">
                {{ booking.fields.Status?.stringValue }}
              </span>
            </td>

            <!-- Notes -->
            <td>
              <div class="notes-preview">
                {{ truncateText(booking.fields.Notes?.stringValue || 'N/A', 60) }}
                <button v-if="(booking.fields.Notes?.stringValue || '').length > 60" class="btn-text" @click="viewBookingDetails(booking)">
                  Read more
                </button>
              </div>
            </td>

            <!-- Payment -->
            <td>
              <span class="payment-amount">${{ booking.fields.PaymentAmt?.doubleValue }}</span>
            </td>

            <!-- Actions -->
            <td>
              <!-- Pending Booking Actions -->
              <div v-if="booking.fields.Status?.stringValue === 'Pending'" class="action-buttons">
                <button @click="cancelBooking(booking.fields.BID?.stringValue)" class="btn-cancel" :disabled="isActionProcessing(booking.fields.BID?.stringValue)">
                  <span v-if="isActionProcessing(booking.fields.BID?.stringValue)" class="input-loader"></span>
                  <span v-else>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="15" y1="9" x2="9" y2="15"></line>
                      <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                  </span>
                  Cancel
                </button>
              </div>

              <!-- View Details for Other Statuses -->
              <button v-else class="btn-details" @click="viewBookingDetails(booking)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                View Details
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Analytics Section -->
    <section class="analytics-section">
      <h2>Your Activity</h2>
      <div class="analytics-grid">
        <div class="analytics-card">
          <h3>Appointment Status</h3>
          <div class="status-chart">
            <div class="chart-legend">
              <div class="legend-item">
                <span class="legend-color pending-color"></span>
                <span>Pending ({{ bookings.filter(b => b.fields.Status?.stringValue === 'Pending').length }})</span>
              </div>
              <div class="legend-item">
                <span class="legend-color completed-color"></span>
                <span>Completed ({{ bookings.filter(b => b.fields.Status?.stringValue === 'Completed').length }})</span>
              </div>
              <div class="legend-item">
                <span class="legend-color cancelled-color"></span>
                <span>Cancelled ({{ bookings.filter(b => b.fields.Status?.stringValue === 'Cancelled').length }})</span>
              </div>
            </div>
          </div>
        </div>

        <div class="analytics-card">
          <h3>Recent Activity</h3>
          <div class="activity-list">
            <div v-if="bookings.length === 0" class="empty-activity">
              <p>No recent activity</p>
            </div>
            <div v-else class="activity-item" v-for="(booking, index) in bookings.slice(0, 3)" :key="index">
              <div class="activity-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
              </div>
              <div class="activity-details">
                <p class="activity-title">{{ getActivityTitle(booking) }}</p>
                <p class="activity-time">{{ formatDate(booking.fields.StartTime?.timestampValue) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Booking Details Modal -->
    <div v-if="showBookingDetails" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Appointment Details</h3>
          <button class="btn-close" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body" v-if="selectedBooking">
          <div class="detail-group">
            <h4>Patient Information</h4>
            <div class="patient-card">
              <div class="patient-avatar patient-avatar-large">
                {{ getPatientInitials(selectedBooking.fields.PID?.stringValue) }}
              </div>
              <div class="patient-details">
                <p class="patient-name">{{ getPatientName(selectedBooking.fields.PID?.stringValue) }}</p>
                <p class="patient-contact" v-if="getPatientContact(selectedBooking.fields.PID?.stringValue)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                  </svg>
                  {{ getPatientContact(selectedBooking.fields.PID?.stringValue) }}
                </p>
                <p class="patient-location" v-if="getPatientLocation(selectedBooking.fields.PID?.stringValue)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                  </svg>
                  {{ getPatientLocation(selectedBooking.fields.PID?.stringValue) }}
                </p>
              </div>
            </div>
          </div>

          <div class="detail-group">
            <h4>Appointment Information</h4>
            <div class="detail-row">
              <span class="detail-label">Booking ID:</span>
              <span class="detail-value">{{ selectedBooking.fields.BID?.stringValue }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Status:</span>
              <span :class="['status-badge', getStatusClass(selectedBooking.fields.Status?.stringValue)]">
                {{ selectedBooking.fields.Status?.stringValue }}
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Payment:</span>
              <span class="detail-value">${{ selectedBooking.fields.PaymentAmt?.doubleValue }}</span>
            </div>
          </div>

          <div class="detail-group">
            <h4>Schedule</h4>
            <div class="detail-row">
              <span class="detail-label">Date:</span>
              <span class="detail-value">{{ formatDate(selectedBooking.fields.StartTime?.timestampValue) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Time:</span>
              <span class="detail-value">
                {{ formatTime(selectedBooking.fields.StartTime?.timestampValue) }} -
                {{ formatTime(selectedBooking.fields.EndTime?.timestampValue) }}
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Duration:</span>
              <span class="detail-value">
                {{ calculateDuration(selectedBooking.fields.StartTime?.timestampValue, selectedBooking.fields.EndTime?.timestampValue) }}
              </span>
            </div>
          </div>

          <div class="detail-group" v-if="selectedBooking.fields.Notes?.stringValue">
            <h4>Notes</h4>
            <div class="notes-box">
              {{ selectedBooking.fields.Notes?.stringValue }}
            </div>
          </div>
        </div>

        <div class="modal-footer" v-if="selectedBooking">
          <!-- Pending Booking Actions -->
          <div v-if="selectedBooking.fields.Status?.stringValue === 'Pending'" class="modal-action-buttons">
            <button @click="cancelBooking(selectedBooking.fields.BID?.stringValue)" class="btn-secondary" :disabled="isActionProcessing(selectedBooking.fields.BID?.stringValue)">
              <span v-if="isActionProcessing(selectedBooking.fields.BID?.stringValue)" class="input-loader"></span>
              Cancel Appointment
            </button>
          </div>

          <!-- Close button for other statuses -->
          <button v-else class="btn-submit" @click="closeModal">
            Close
          </button>
        </div>
      </div>
    </div>

    <div v-if="showCancellationModal" class="modal-overlay" @click="closeCancellationModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Cancellation Reason</h3>
          <button class="btn-close" @click="closeCancellationModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p class="modal-warning">Oi! You better have a bleedin' good excuse!</p>
          <p>This cancellation will be tracked and the patient will see your reason:</p>
          <textarea
              v-model="cancellationReason"
              class="cancellation-reason-input"
              placeholder="Tell us why you're cancelling this appointment..."
              rows="4"
          ></textarea>
        </div>
        <div class="modal-footer">
          <button @click="closeCancellationModal" class="btn-secondary">
            Nevermind
          </button>
          <button @click="submitCancellationWithReason" class="btn-submit" :disabled="!cancellationReason.trim() || isActionProcessing(selectedBookingId)">
            <span v-if="isActionProcessing(selectedBookingId)" class="input-loader"></span>
            Submit & Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Action Status Toast -->
    <div v-if="actionMessage" :class="['action-toast', actionSuccess ? 'success-toast' : 'error-toast']">
      <span v-if="actionSuccess" class="toast-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
      </span>
      <span v-else class="toast-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      </span>
      <span class="toast-message">{{ actionMessage }}</span>
      <button class="toast-close" @click="dismissActionMessage">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

export default {
  name: 'BookingManager',
  components: {
    VueDatePicker,
  },
  data() {
    return {
      // Authentication and loading states
      loggedIn: false,
      isLoadingBookings: false,
      isLoadingNurses: false,
      isLoadingPatients: false,

      showCancellationModal: false,
      cancellationReason: '',
      selectedBookingId: null,

      // Data stores
      bookings: [],
      nurses: [],
      patients: [],
      selectedNurse: null,

      // UI controls
      statusFilter: 'all',
      searchQuery: '',
      showBookingDetails: false,
      selectedBooking: null,

      // Processing state tracking
      processingActions: {}, // Keys are booking IDs, values are boolean (true = processing)

      // Notification states
      actionMessage: '',
      actionSuccess: false,
      actionMessageTimer: null
    }
  },
  computed: {
    filteredBookings() {
      let result = [...this.bookings];

      // Apply status filter
      if (this.statusFilter !== 'all') {
        result = result.filter(booking =>
            booking.fields.Status?.stringValue === this.statusFilter
        );
      }

      // Apply search query
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(booking => {
          const nurseMatch = this.nurses.find(
              n => n.NID === booking.fields.NID?.stringValue
          )?.name.toLowerCase().includes(query);

          const bidMatch = booking.fields.BID?.stringValue?.toLowerCase().includes(query);
          const notesMatch = booking.fields.Notes?.stringValue?.toLowerCase().includes(query);

          return nurseMatch || bidMatch || notesMatch;
        });
      }

      // Sort bookings by date & time (StartTime)
      result.sort((a, b) => {
        const timeA = new Date(a.fields.StartTime?.timestampValue || 0);
        const timeB = new Date(b.fields.StartTime?.timestampValue || 0);
        return timeA - timeB;
      });

      return result;
    }
  },
  methods: {
    // Authentication methods
    login() {
      this.loggedIn = true;
      this.getBookings();
    },

    // Data fetching methods
    getCurrentNurse() {
      this.isLoadingNurses = true;

      axios.get(`http://localhost:5003/api/nurses/${localStorage.getItem('userId')}`)
          .then(response => {
            this.selectedNurse = response.data;
            this.login();
          })
          .catch(error => {
            console.error("Error fetching nurse information:", error);
            this.showActionMessage("Failed to load your profile. Please refresh the page.", false);
          })
          .finally(() => {
            this.isLoadingNurses = false;
          });
    },

    getAllNurses() {
      this.isLoadingNurses = true;

      axios.get('http://localhost:5003/api/nurses/')
          .then(response => {
            this.nurses = response.data;
            this.selectedNurse = this.nurses.find((element) => element.NID === localStorage.getItem('userId'));
            this.login();
          })
          .catch(error => {
            console.error("Error fetching nurses:", error);
            this.showActionMessage("Failed to load nurse information.", false);
          })
          .finally(() => {
            this.isLoadingNurses = false;
          });
    },

    getAllPatients() {
      this.isLoadingPatients = true;

      axios.get('https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/GetAllPatients')
          .then(response => {
            this.patients = response.data.Patients;
          })
          .catch(error => {
            console.error("Error fetching patients:", error);
            this.showActionMessage("Failed to load patient information.", false);
          })
          .finally(() => {
            this.isLoadingPatients = false;
          });
    },

    getBookings() {
      this.isLoadingBookings = true;

      if (!this.selectedNurse || !this.selectedNurse.NID) {
        this.isLoadingBookings = false;
        this.showActionMessage("Unable to fetch appointments: Nurse information not available.", false);
        return;
      }

      axios.get(`https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/GetBookingsForNurse/${this.selectedNurse.NID}`)
          .then(response => {
            this.bookings = response.data.Bookings || [];
          })
          .catch(error => {
            console.error("Error fetching bookings:", error);
            this.showActionMessage("Failed to load your appointments.", false);
          })
          .finally(() => {
            this.isLoadingBookings = false;
          });
    },

    // Booking action methods
    cancelBooking(bid) {
      this.selectedBookingId = bid;
      this.cancellationReason = '';
      this.showCancellationModal = true;
    },

    closeCancellationModal() {
      this.showCancellationModal = false;
      this.cancellationReason = '';
      this.selectedBookingId = null;
    },

    submitCancellationWithReason() {
      if (!this.cancellationReason.trim()) {
        this.showActionMessage("Oi! Give us a proper reason, ya mug!", false);
        return;
      }

      this.setActionProcessing(this.selectedBookingId, true);

      const data = {
        bookingId: this.selectedBookingId,
        nurseId: this.selectedNurse.NID,  // Add the nurse ID from yer selected nurse
        reason: this.cancellationReason
      };

      axios.post('http://localhost:5011/api/cancel-booking/nurse-cancel', data)
          .then(() => {
            this.showActionMessage("Sorted! Appointment cancelled and reassigned.", true);
            this.getBookings();
            this.closeCancellationModal();
          })
          .catch(error => {
            console.error("Error cancelling booking with reason:", error);
            this.showActionMessage("Bloody 'ell! Something went wrong. Try again!", false);
          })
          .finally(() => {
            this.setActionProcessing(this.selectedBookingId, false);
          });
    },

    // UI interaction methods
    viewBookingDetails(booking) {
      this.selectedBooking = booking;
      this.showBookingDetails = true;
    },

    viewPatientInfo(patientId) {
      const booking = this.bookings.find(b => b.fields.PID?.stringValue === patientId);
      if (booking) {
        this.viewBookingDetails(booking);
      }
    },

    closeModal() {
      this.showBookingDetails = false;
      this.selectedBooking = null;
    },

    resetFilters() {
      this.statusFilter = 'all';
      this.searchQuery = '';
    },

    // Status tracking methods
    isActionProcessing(bookingId) {
      return this.processingActions[bookingId] === true;
    },

    setActionProcessing(bookingId, isProcessing) {
      if (isProcessing) {
        // Using standard object assignment which works with Vue 3 reactivity
        this.processingActions[bookingId] = true;
      } else {
        // Delete operator works directly in Vue 3
        delete this.processingActions[bookingId];
      }
    },

    // Notification methods
    showActionMessage(message, isSuccess) {
      // Clear any existing timer
      if (this.actionMessageTimer) {
        clearTimeout(this.actionMessageTimer);
      }

      this.actionMessage = message;
      this.actionSuccess = isSuccess;

      // Auto dismiss after 5 seconds
      this.actionMessageTimer = setTimeout(() => {
        this.dismissActionMessage();
      }, 5000);
    },

    dismissActionMessage() {
      this.actionMessage = '';
      if (this.actionMessageTimer) {
        clearTimeout(this.actionMessageTimer);
        this.actionMessageTimer = null;
      }
    },

    // Helper/formatting methods
    truncateText(text, maxLength) {
      if (!text) return 'N/A';
      if (text.length <= maxLength) return text;
      return text.substring(0, maxLength) + '...';
    },

    formatDate(timestamp) {
      if (!timestamp) return 'N/A';

      const date = new Date(timestamp);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        weekday: 'short'
      }).format(date);
    },

    formatTime(timestamp) {
      if (!timestamp) return '';

      const date = new Date(timestamp);
      return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    },

    formatDateTime(timestamp) {
      if (!timestamp) return 'N/A';

      const date = new Date(timestamp);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    },

    calculateDuration(startTime, endTime) {
      if (!startTime || !endTime) return 'N/A';

      const start = new Date(startTime);
      const end = new Date(endTime);

      const diffMs = end - start;
      const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMins = Math.round((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      if (diffHrs === 0) {
        return `${diffMins} minutes`;
      } else if (diffMins === 0) {
        return `${diffHrs} hour${diffHrs !== 1 ? 's' : ''}`;
      } else {
        return `${diffHrs} hour${diffHrs !== 1 ? 's' : ''} ${diffMins} min`;
      }
    },

    getStatusClass(status) {
      if (!status) return '';

      const statusMap = {
        'Pending': 'status-pending',
        'Completed': 'status-completed',
        'Cancelled': 'status-cancelled'
      };

      return statusMap[status] || '';
    },

    // Patient information helpers
    getPatientName(patientId) {
      const patient = this.patients.find(p => p.PID === patientId);
      return patient ? patient.Name : 'Unknown Patient';
    },

    getPatientInitials(patientId) {
      const name = this.getPatientName(patientId);
      if (!name || name === 'Unknown Patient') return 'UP';

      const nameParts = name.split(' ');
      if (nameParts.length >= 2) {
        return `${nameParts[0][0]}${nameParts[1][0]}`;
      }
      return nameParts[0].substring(0, 2).toUpperCase();
    },

    getPatientContact(patientId) {
      const patient = this.patients.find(p => p.PID === patientId);
      return patient?.PhoneNum || patient?.Email || '';
    },

    getPatientLocation(patientId) {
      const patient = this.patients.find(p => p.PID === patientId);
      return patient?.Location || '';
    },

    // Activity section helpers
    getActivityTitle(booking) {
      const status = booking.fields.Status?.stringValue;
      const patient = this.getPatientName(booking.fields.PID?.stringValue);

      switch(status) {
        case 'Pending':
          return `New appointment request from ${patient}`;
        case 'Completed':
          return `Appointment with ${patient} completed`;
        case 'Cancelled':
          return `Appointment with ${patient} cancelled`;
        default:
          return `Appointment update from ${patient}`;
      }
    }
  },
  created() {
    // Initial load of data
    this.getAllPatients();
    this.getAllNurses();
    // Alternative: this.getCurrentNurse();
  }
}
</script>

<style scoped>
.booking-container {
  --primary: #4361ee;
  --primary-light: #edf2ff;
  --secondary: #3a0ca3;
  --accent: #f72585;
  --success: #10b981;
  --warning: #fbbf24;
  --danger: #ef4444;
  --neutral-100: #f8fafc;
  --neutral-200: #e2e8f0;
  --neutral-300: #cbd5e1;
  --neutral-400: #94a3b8;
  --neutral-500: #64748b;
  --neutral-600: #475569;
  --neutral-700: #334155;
  --neutral-800: #1e293b;
  --neutral-900: #0f172a;
  --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  --card-shadow-hover: 0 8px 20px rgba(0, 0, 0, 0.12);
  --transition: all 0.3s ease;
}

* {
  box-sizing: border-box;
}

/* Loading Container */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 32px;
  text-align: center;
  background: #f0f4f8;
}

.loading-container h2 {
  margin-top: 24px;
  margin-bottom: 8px;
  color: var(--secondary);
  font-size: 24px;
}

.loading-container p {
  color: var(--neutral-600);
  font-size: 16px;
  max-width: 400px;
}

.loader-large {
  width: 48px;
  height: 48px;
  border-width: 4px;
}

/* Main Container */
.booking-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 28px;
  padding: 32px;
  background: #f0f4f8;
  max-width: 1200px;
  margin: 0 auto;
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--neutral-800);
}

/* Dashboard Header */
.dashboard-header {
  grid-column: 1 / -1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: var(--card-shadow);
}

.user-welcome h1 {
  margin: 0;
  color: var(--secondary);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.subtitle {
  color: var(--neutral-600);
  margin-top: 4px;
  font-size: 15px;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 100px;
  padding: 12px 16px;
  background-color: var(--primary-light);
  border-radius: 8px;
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--neutral-700);
  margin-top: 4px;
}

/* Sections */
section {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: none;
  box-shadow: var(--card-shadow);
  transition: var(--transition);
}

section:hover {
  box-shadow: var(--card-shadow-hover);
}

section h2 {
  margin-top: 0;
  color: var(--neutral-800);
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 24px;
  border-bottom: 2px solid var(--primary-light);
  padding-bottom: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-badge {
  background-color: var(--primary-light);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 50px;
}

/* Button styling */
.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 6px;
}

.btn-text {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 14px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: var(--transition);
}

.btn-text:hover {
  background-color: var(--primary-light);
  color: var(--secondary);
}

.btn-secondary {
  padding: 10px 16px;
  border: 1px solid var(--neutral-300);
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  background-color: white;
  color: var(--neutral-700);
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  margin-right: 12px;
}

.btn-secondary:hover {
  border-color: var(--neutral-400);
  background-color: var(--neutral-100);
}

.btn-refresh,
.btn-submit {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  background-color: #4361ee; /* Primary blue */
  color: white;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(67, 97, 238, 0.2);
}

.btn-refresh:hover,
.btn-submit:hover {
  background-color: hotpink;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(67, 97, 238, 0.3);
}

.btn-refresh:active,
.btn-submit:active {
  transform: translateY(0);
}

.btn-refresh:disabled,
.btn-submit:disabled {
  background-color: var(--neutral-400);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-link {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 14px;
  font-weight: 500;
  padding: 6px 12px;
  cursor: pointer;
  text-decoration: underline;
}

.btn-cancel {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background-color: #fef2f2;
  color: #b91c1c;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  transition: var(--transition);
}

.btn-details {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background-color: var(--neutral-100);
  color: var(--neutral-700);
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  transition: var(--transition);
}

.btn-cancel:hover {
  background-color: #fee2e2;
}

.btn-details:hover {
  background-color: var(--neutral-200);
}

.btn-cancel:disabled, .btn-details:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Table Actions */
.table-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.table-filter {
  width: 180px;
}

.filter-select {
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--neutral-300);
  font-size: 14px;
  color: var(--neutral-700);
  background-color: white;
}

.table-search {
  width: 250px;
}

.search-input-wrapper {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--neutral-500);
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border-radius: 6px;
  border: 1px solid var(--neutral-300);
  font-size: 14px;
  color: var(--neutral-700);
  background-color: white;
}

/* Table */
.table-responsive {
  overflow-x: auto;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 12px;
  background: #fff;
  font-size: 14px;
  border-radius: 8px;
  overflow: hidden;
}

th, td {
  border: none;
  border-bottom: 1px solid var(--neutral-200);
  padding: 14px 16px;
  text-align: left;
}

th {
  background-color: var(--primary-light);
  font-weight: 600;
  color: var(--neutral-800);
  position: sticky;
  top: 0;
}

th:first-child {
  border-top-left-radius: 8px;
}

th:last-child {
  border-top-right-radius: 8px;
}

tr:last-child td {
  border-bottom: none;
}

tr:nth-child(even) {
  background-color: var(--neutral-100);
}

tr:hover {
  background-color: var(--primary-light);
}

/* Patient Info */
.patient-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: var(--transition);
}

.patient-info:hover {
  background-color: var(--primary-light);
}

.patient-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.patient-avatar-large {
  width: 48px;
  height: 48px;
  font-size: 16px;
}

.patient-details {
  flex: 1;
}

.patient-name {
  margin: 0;
  font-weight: 500;
  color: var(--neutral-800);
  line-height: 1.2;
}

.booking-id {
  margin: 0;
  font-family: monospace;
  color: var(--neutral-600);
  font-size: 12px;
}

/* Booking Time */
.booking-time {
  display: flex;
  flex-direction: column;
}

.booking-time .date {
  font-weight: 500;
  color: var(--neutral-800);
  margin: 0;
}

.booking-time .time {
  color: var(--neutral-600);
  font-size: 13px;
  margin: 4px 0;
}

.booking-time .duration {
  color: var(--neutral-500);
  font-size: 12px;
  margin: 0;
}

/* Status Badge */
.status-badge {
  padding: 6px 10px;
  border-radius: 50px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
  border: 1px solid transparent;
}

.status-pending {
  background-color: #fff8e6;
  color: #92400e;
  border-color: #fde68a;
}

.status-completed {
  background-color: #eff6ff;
  color: #1e40af;
  border-color: #bfdbfe;
}

.status-cancelled {
  background-color: #fef2f2;
  color: #b91c1c;
  border-color: #fecaca;
}

/* Notes Preview */
.notes-preview {
  line-height: 1.4;
  color: var(--neutral-700);
}

/* Payment Amount */
.payment-amount {
  font-weight: 500;
  color: var(--neutral-700);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 8px;
}

/* Calendar Placeholder */
.calendar-placeholder {
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--neutral-100);
  border-radius: 8px;
  border: 1px dashed var(--neutral-300);
  text-align: center;
}

.calendar-placeholder svg {
  color: var(--neutral-400);
  margin-bottom: 16px;
}

.calendar-placeholder p {
  margin: 0;
  color: var(--neutral-600);
}

.calendar-placeholder .hint-text {
  font-size: 14px;
  color: var(--neutral-500);
  margin-top: 8px;
}

/* Analytics Section */
.analytics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.analytics-card {
  padding: 16px;
  background-color: var(--neutral-100);
  border-radius: 8px;
  border: 1px solid var(--neutral-200);
}

.analytics-card h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  color: var(--neutral-700);
  font-weight: 600;
}

.chart-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--neutral-700);
}

.legend-color {
  width: 20px;
  height: 10px;
  border-radius: 2px;
}

.pending-color {
  background-color: #fde68a;
}

.completed-color {
  background-color: #2354ee;;
}

.cancelled-color {
  background-color: #fecaca;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background-color: white;
  border-radius: 6px;
  border: 1px solid var(--neutral-200);
}

.activity-icon {
  width: 28px;
  height: 28px;
  background-color: var(--primary-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.activity-details {
  flex: 1;
}

.activity-title {
  margin: 0 0 4px 0;
  font-weight: 500;
  color: var(--neutral-800);
}

.activity-time {
  margin: 0;
  font-size: 12px;
  color: var(--neutral-500);
}

.empty-activity {
  text-align: center;
  padding: 20px;
  color: var(--neutral-500);
}

/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--neutral-200);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--neutral-800);
}

.btn-close {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--neutral-500);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}

.btn-close:hover {
  background-color: var(--neutral-100);
  color: var(--neutral-800);
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--neutral-200);
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.modal-action-buttons {
  display: flex;
  align-items: center;
}

.detail-group {
  margin-bottom: 24px;
}

.detail-group h4 {
  font-size: 16px;
  color: var(--neutral-700);
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--neutral-200);
}

.detail-row {
  display: flex;
  margin-bottom: 8px;
  font-size: 15px;
}

.detail-label {
  min-width: 100px;
  color: var(--neutral-600);
}

.detail-value {
  font-weight: 500;
  color: var(--neutral-800);
}

.notes-box {
  background-color: var(--neutral-100);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.5;
}

.patient-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: var(--primary-light);
  border-radius: 8px;
  margin-bottom: 8px;
}

.patient-contact, .patient-location {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--neutral-600);
  margin: 8px 0 0 0;
}

.action-text {
  color: var(--neutral-700);
  background-color: #fff8e6;
  border-left: 3px solid #fbbf24;
  padding: 12px 16px;
  border-radius: 4px;
  margin: 0;
}

/* Toast Message */
.action-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  max-width: 400px;
  animation: slide-in 0.3s ease;
}

@keyframes slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.success-toast {
  background-color: #ecfdf5;
  border-left: 4px solid #10b981;
  color: #065f46;
}

.error-toast {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
  color: #b91c1c;
}

.toast-icon {
  flex-shrink: 0;
}

.toast-message {
  font-size: 14px;
  font-weight: 500;
  margin-right: 12px;
}

.toast-close {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  border-radius: 4px;
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-close:hover {
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.05);
}

/* Loading indicators */
.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.loader {
  border: 3px solid var(--neutral-200);
  border-top: 3px solid var(--primary);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.input-loader {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

.spin-loader {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Empty state styling */
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: var(--neutral-500);
  background-color: var(--neutral-100);
  border-radius: 8px;
  border: 1px dashed var(--neutral-300);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-state svg {
  margin-bottom: 16px;
  color: var(--neutral-400);
}

.empty-state p {
  margin: 0;
  font-size: 15px;
}

.empty-state .hint-text {
  margin-top: 8px;
  font-size: 14px;
  color: var(--neutral-400);
}

/* Responsive Design */
@media (min-width: 768px) {
  .booking-container {
    grid-template-columns: 2fr 1fr;
  }

  .dashboard-header,
  .view-bookings {
    grid-column: 1 / -1; /* Span across all columns */
  }

  .analytics-section {
    grid-column: 1 / -1; /* Span across all columns */
  }
}

@media (max-width: 992px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .booking-container {
    padding: 16px;
    gap: 20px;
  }

  section {
    padding: 16px;
  }

  .dashboard-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-stats {
    width: 100%;
    justify-content: center;
  }

  .table-actions {
    flex-direction: column;
    gap: 12px;
  }

  .table-filter, .table-search {
    width: 100%;
  }

  .action-buttons {
    flex-direction: column;
    gap: 8px;
  }

  .action-buttons button {
    width: 100%;
  }

  .modal-action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .modal-action-buttons button {
    width: 100%;
    margin-right: 0;
    margin-bottom: 8px;
  }

  .modal-content {
    max-height: 95vh;
  }

  .action-toast {
    max-width: calc(100% - 32px);
    left: 16px;
    right: 16px;
  }
}
.cancellation-reason-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--neutral-300);
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  margin-top: 8px;
}

.cancellation-reason-input:focus {
  border-color: var(--primary);
  outline: none;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2);
}

.modal-warning {
  color: var(--danger);
  font-weight: 600;
  border-left: 3px solid var(--danger);
  padding-left: 12px;
  margin-bottom: 16px;
}
</style>