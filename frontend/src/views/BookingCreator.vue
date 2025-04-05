<template>
  <!-- Loading State Section -->
  <div v-if="!loggedIn" class="loading-container">
    <div class="loader loader-large"></div>
    <h2>Loading Your Patient Dashboard</h2>
    <p>Please wait while we retrieve your information...</p>
  </div>

  <!-- Main Content Section -->
  <div v-else class="booking-container">
    <!-- Header Section -->
    <header class="dashboard-header">
      <div class="user-welcome">
        <h1>Welcome, {{ selectedPatient.Name }}</h1>
        <p class="subtitle">Manage your healthcare appointments in one place</p>
      </div>
      <div class="header-stats">
        <div class="stat-card">
          <span class="stat-number">{{ bookings.length }}</span>
          <span class="stat-label">Total Bookings</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{ bookings.filter(b => b.fields.Status?.stringValue === 'Pending').length }}</span>
          <span class="stat-label">Pending</span>
        </div>
      </div>
    </header>

    <!-- View Bookings Section -->
    <section class="view-bookings">
      <div class="section-header">
        <div class="section-title">
          <h2>Your Appointments</h2>
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
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="16" y1="2" x2="16" y2="6"></line>
          <line x1="8" y1="2" x2="8" y2="6"></line>
          <line x1="3" y1="10" x2="21" y2="10"></line>
        </svg>
        <p>You don't have any appointments yet.</p>
        <p class="hint-text">Create your first appointment using the form below.</p>
      </div>

      <!-- Bookings Table -->
      <div v-else class="table-responsive">
        <div class="table-actions">
          <div class="table-filter">
            <select v-model="statusFilter" class="filter-select">
              <option value="all">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Accepted">Accepted</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div class="table-search">
            <input type="text" placeholder="Search..." v-model="searchQuery" class="search-input">
          </div>
        </div>

        <table>
          <thead>
          <tr>
            <th>Booking ID</th>
            <th>Nurse</th>
            <th>Date & Time</th>
            <th>Duration</th>
            <th>Status</th>
            <th>Payment</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(booking, index) in filteredBookings" :key="index">
            <td>
              <span class="booking-id">{{ booking.fields.BID?.stringValue }}</span>
            </td>
            <td>
              <div class="nurse-info">
                <div class="nurse-avatar">{{ getNurseInitials(booking.fields.NID?.stringValue) }}</div>
                <span>{{ getNurseName(booking.fields.NID?.stringValue) }}</span>
              </div>
            </td>
            <td>
              <div class="booking-time">
                <div class="date">{{ formatDate(booking.fields.StartTime?.timestampValue) }}</div>
                <div class="time">{{ formatTime(booking.fields.StartTime?.timestampValue) }}</div>
              </div>
            </td>
            <td>{{ calculateDuration(booking.fields.StartTime?.timestampValue, booking.fields.EndTime?.timestampValue) }}</td>
            <td>
              <span :class="['status-badge', getStatusClass(booking.fields.Status?.stringValue)]">
                {{ booking.fields.Status?.stringValue }}
              </span>
            </td>
            <td>
              <span class="payment-amount">${{ booking.fields.PaymentAmt?.doubleValue }}</span>
            </td>
            <td>
              <div class="action-buttons">
                <button class="btn-icon" @click="viewBookingDetails(booking)" title="View Details">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
                <button v-if="booking.fields.Status?.stringValue === 'Pending'" class="btn-icon btn-cancel" @click="cancelBooking(booking)" title="Cancel">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Create Booking Section -->
    <section class="create-booking">
      <h2>Schedule New Appointment</h2>

      <form @submit.prevent="createBooking">
        <!-- Date & Time Selection -->
        <div class="form-section">
          <h3 class="form-section-title">1. Choose Date & Time</h3>

          <div class="form-row">
            <div class="form-group">
              <label for="startTime">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="input-icon">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                Start Time
              </label>
              <VueDatePicker
                  id="startTime"
                  v-model="newBooking.StartTime"
                  :required="true"
                  :enableTimePicker="true"
                  :clearable="false"
                  placeholder="Select start time"
                  class="date-picker"
              />
            </div>

            <div class="form-group">
              <label for="endTime">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="input-icon">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                End Time
              </label>
              <VueDatePicker
                  id="endTime"
                  v-model="newBooking.EndTime"
                  :required="true"
                  :enableTimePicker="true"
                  :clearable="false"
                  placeholder="Select end time"
                  class="date-picker"
              />
            </div>
          </div>
        </div>

        <!-- Nurse Assignment -->
        <div class="form-section">
          <h3 class="form-section-title">2. Nurse Information</h3>

          <div class="nurse-card" v-if="selectedNurse">
            <div class="nurse-details">
              <p class="nurse-name">{{ selectedNurse.name }}</p>
              <p class="nurse-availability" v-if="selectedNurse.availableTiming">{{ selectedNurse.availableTiming }}</p>
              <button type="button" class="btn-text" @click="randomNurse">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                  <line x1="12" y1="22.08" x2="12" y2="12"></line>
                </svg>
                Assign Different Nurse
              </button>
            </div>
          </div>

          <div v-else class="loading-nurse">
            <div class="loader input-loader"></div>
            <p>Assigning a nurse...</p>
          </div>
        </div>

        <!-- Additional Information -->
        <div class="form-section">
          <h3 class="form-section-title">3. Appointment Details</h3>

          <div class="form-group">
            <label for="notes">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="input-icon">
                <line x1="21" y1="10" x2="3" y2="10"></line>
                <line x1="21" y1="6" x2="3" y2="6"></line>
                <line x1="21" y1="14" x2="3" y2="14"></line>
                <line x1="21" y1="18" x2="3" y2="18"></line>
              </svg>
              Notes and Requirements
            </label>
            <textarea
                id="notes"
                v-model="newBooking.Notes"
                placeholder="Describe your needs or any special requirements for this appointment"
                rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="paymentAmt">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="input-icon">
                <line x1="12" y1="1" x2="12" y2="23"></line>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
              </svg>
              Payment Amount
            </label>
            <div class="input-prefix">
              <span class="currency-symbol">$</span>
              <input
                  type="number"
                  step="0.01"
                  id="paymentAmt"
                  v-model="newBooking.PaymentAmt"
                  placeholder="0.00"
                  required
              />
            </div>
          </div>
        </div>

        <!-- Submit Section -->
        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="resetForm">
            Reset
          </button>
          <button type="submit" class="btn-submit" :disabled="isCreatingBooking">
            {{ isCreatingBooking ? 'Scheduling...' : 'Schedule Appointment' }}
          </button>
        </div>
      </form>

      <div v-if="createMessage" :class="['message', createSuccess ? 'success' : 'error']">
        {{ createMessage }}
      </div>
    </section>

    <!-- Profile Section -->
    <section class="profile-section">
      <div class="section-header">
        <h2>Your Profile</h2>
        <button class="btn-text">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
          Edit Profile
        </button>
      </div>

      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar-placeholder">
            {{ getInitials(selectedPatient.Name) }}
          </div>
          <h3 class="profile-name">{{ selectedPatient.Name }}</h3>
        </div>

        <div class="profile-info">
          <div class="info-group">
            <p class="info-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="info-icon">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
              </svg>
              Email
            </p>
            <p class="info-value">{{ selectedPatient.Email }}</p>
          </div>

          <div class="info-group">
            <p class="info-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="info-icon">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
              </svg>
              Phone
            </p>
            <p class="info-value">{{ selectedPatient.PhoneNum }}</p>
          </div>

          <div class="info-group">
            <p class="info-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="info-icon">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
              Location
            </p>
            <p class="info-value">{{ selectedPatient.Location }}</p>
          </div>

          <div class="info-group">
            <p class="info-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="info-icon">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                <polyline points="13 2 13 9 20 9"></polyline>
              </svg>
              Medical Records
            </p>
            <p class="info-value medical-record">{{ selectedPatient.MedicalRecord }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Booking Details Modal -->
    <div v-if="showBookingDetails" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Booking Details</h3>
          <button class="btn-close" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body" v-if="selectedBooking">
          <div class="detail-group">
            <h4>Booking Information</h4>
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
              <span class="detail-label">Start:</span>
              <span class="detail-value">{{ formatDateTime(selectedBooking.fields.StartTime?.timestampValue) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">End:</span>
              <span class="detail-value">{{ formatDateTime(selectedBooking.fields.EndTime?.timestampValue) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Duration:</span>
              <span class="detail-value">{{ calculateDuration(selectedBooking.fields.StartTime?.timestampValue, selectedBooking.fields.EndTime?.timestampValue) }}</span>
            </div>
          </div>

          <div class="detail-group">
            <h4>Nurse Information</h4>
            <div class="nurse-card">
              <div class="nurse-avatar nurse-avatar-medium">
                {{ getNurseInitials(selectedBooking.fields.NID?.stringValue) }}
              </div>
              <div class="nurse-details">
                <p class="nurse-name">{{ getNurseName(selectedBooking.fields.NID?.stringValue) }}</p>
              </div>
            </div>
          </div>

          <div class="detail-group" v-if="selectedBooking.fields.Notes?.stringValue">
            <h4>Notes</h4>
            <div class="notes-box">
              {{ selectedBooking.fields.Notes?.stringValue }}
            </div>
          </div>
        </div>
        <div class="modal-footer" v-if="selectedBooking && selectedBooking.fields.Status?.stringValue === 'Pending'">
          <button class="btn-secondary" @click="cancelBooking(selectedBooking)">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            Cancel Booking
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

export default {
  name: 'Booking',
  components: {
    VueDatePicker,
  },
  data() {
    return {
      loggedIn: false,
      bookings: [],
      nurses: [],
      patients: [],
      selectedPatient: null,
      selectedNurse: null,
      isLoadingBookings: false,
      isLoadingNurses: false,
      isLoadingPatients: false,
      isCreatingBooking: false,
      isAcceptingBooking: false,
      newBooking: {
        PID: '',
        NID: '',
        StartTime: '',
        EndTime: '',
        APIKey: '',
        Notes: '',
        PaymentAmt: 0
      },
      acceptData: {
        bid: '',
        APIKey: ''
      },
      createMessage: '',
      createSuccess: false,
      acceptMessage: '',
      acceptSuccess: false,

      // New properties for enhanced UI
      statusFilter: 'all',
      searchQuery: '',
      showBookingDetails: false,
      selectedBooking: null
    }
  },
  methods: {
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
    formatDate(timestamp) {
      if (!timestamp) return 'N/A';

      const date = new Date(timestamp);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
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

// For nurse information
    getNurseInitials(nurseId) {
      const nurse = this.nurses.find(n => n.NID === nurseId);
      if (!nurse) return 'N/A';

      const nameParts = nurse.name.split(' ');
      if (nameParts.length >= 2) {
        return `${nameParts[0][0]}${nameParts[1][0]}`;
      }
      return nameParts[0].substring(0, 2).toUpperCase();
    },

    getNurseName(nurseId) {
      const nurse = this.nurses.find(n => n.NID === nurseId);
      return nurse ? nurse.name : 'Unknown Nurse';
    },

// For patient information
    getInitials(name) {
      if (!name) return '';

      const nameParts = name.split(' ');
      if (nameParts.length >= 2) {
        return `${nameParts[0][0]}${nameParts[1][0]}`;
      }
      return nameParts[0].substring(0, 2).toUpperCase();
    },

// For modal functionality
    viewBookingDetails(booking) {
      this.selectedBooking = booking;
      this.showBookingDetails = true;
    },

    closeModal() {
      this.showBookingDetails = false;
      this.selectedBooking = null;
    },

// Form management
    resetForm() {
      this.newBooking = {
        PID: '',
        NID: '',
        StartTime: '',
        EndTime: '',
        APIKey: '',
        Notes: '',
        PaymentAmt: 0
      };
      this.randomNurse();
    },

// For booking table filtering
    cancelBooking(booking) {
      // Implement booking cancellation logic here
      console.log("Cancelling booking:", booking.fields.BID?.stringValue);
      // After implementation:
      // this.getBookings();
      this.closeModal();
    },

    getStatusClass(status) {
      if (!status) return '';

      const statusMap = {
        'Pending': 'status-pending',
        'Accepted': 'status-accepted',
        'Completed': 'status-completed',
        'Cancelled': 'status-cancelled'
      };

      return statusMap[status] || '';
    },

    login() {
      this.loggedIn = true;
      this.getBookings();
    },

    getBookings() {
      this.isLoadingBookings = true;

      axios
          .get('https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/GetBookingsFromUser/' + this.selectedPatient.PID)
          .then(response => {
            this.bookings = response.data.Bookings || [];
          })
          .catch(error => {
            console.error("Error fetching bookings:", error);
          })
          .finally(() => {
            this.isLoadingBookings = false;
          });
    },

    getAllNurses() {
      this.isLoadingNurses = true;

      axios
          .get('http://localhost:5003/api/nurses/')
          .then(response => {
            this.nurses = response.data;
            this.randomNurse();
          })
          .catch(error => {
            console.error("Error fetching nurses:", error);
          })
          .finally(() => {
            this.isLoadingNurses = false;
          });
    },

    getAllPatients() {
      this.isLoadingPatients = true;

      axios
          .get('https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/GetAllPatients')
          .then(response => {
            this.patients = response.data.Patients
            this.selectedPatient = this.patients.find((element) => element.PID === localStorage.getItem('userId'))
            this.login();
          })
          .catch(error => {
            console.error("Error fetching patients:", error);
          })
          .finally(() => {
            this.isLoadingPatients = false;
          });
    },

    getCurrentPatient() {
      this.isLoadingPatients = true;

      axios
          .get('https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/GetPatient/' + localStorage.getItem('userId'))
          .then(response => {
            this.selectedPatient = response.data.Patient
            this.login();
          })
          .catch(error => {
            console.error("Error fetching patients:", error);
          })
          .finally(() => {
            this.isLoadingPatients = false;
          });
    },

    createBooking() {
      this.isCreatingBooking = true;
      this.createMessage = '';
      this.newBooking.PID = this.selectedPatient.PID
      this.newBooking.NID = this.selectedNurse.NID

      axios
          .post(
              'http://localhost:5008/v1/MakeBooking',
              this.newBooking
          )
          .then(() => {
            this.createMessage = "Booking created successfully!";
            this.createSuccess = true;
            this.getBookings();

            // Reset form
            this.newBooking = {
              PID: '',
              NID: '',
              StartTime: '',
              EndTime: '',
              APIKey: '',
              Notes: '',
              PaymentAmt: 0
            };
          })
          .catch(error => {
            console.error("Error creating booking:", error);
            this.createMessage = "Error creating booking. Please try again.";
            this.createSuccess = false;
          })
          .finally(() => {
            this.isCreatingBooking = false;
          });
    },
    randomNurse() {
      if (true) {
        var ranNum = Math.floor(Math.random() * (this?.nurses?.length - 1 + 1))
        this.newBooking.NID = this?.nurses[ranNum]?.NID;
        this.selectedNurse = this?.nurses[ranNum];
      }
    }
  },
  created() {
    // Initial load of data with loading states
    // this.getBookings();
    this.getCurrentPatient();
    this.getAllNurses();
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

      return result;
    }
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
  background-color: white;
  border: 1px solid #e2e8f0;
  color: #475569;
}

.btn-secondary:hover {
  border-color: var(--neutral-400);
  background-color: var(--neutral-100);
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

/* Form styling */
.form-group {
  margin-bottom: 16px;
  width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 8px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--neutral-700);
  font-size: 14px;
}

input, textarea, select {
  padding: 12px 16px;
  width: 100%;
  font-size: 15px;
  border: 1px solid var(--neutral-300);
  border-radius: 8px;
  background-color: #fff;
  transition: var(--transition);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: var(--neutral-800);
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15);
}

textarea,
input[type="number"],
input[type="text"] {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

/* Button styling */
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

.form-actions {
  margin-top: 28px;
  display: flex;
  justify-content: flex-end;
}

/* Table styles */
.table-responsive {
  overflow-x: auto;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

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
  width: 220px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--neutral-300);
  font-size: 14px;
  color: var(--neutral-700);
  background-color: white;
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

.booking-id {
  font-family: monospace;
  color: var(--neutral-600);
  font-size: 13px;
}

.nurse-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nurse-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
}

.nurse-avatar-medium {
  width: 40px;
  height: 40px;
  font-size: 14px;
}

.nurse-avatar-large {
  width: 60px;
  height: 60px;
  font-size: 18px;
}

.booking-time {
  display: flex;
  flex-direction: column;
}

.booking-time .date {
  font-weight: 500;
}

.booking-time .time {
  color: var(--neutral-600);
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 5px;
}

.action-buttons .btn-icon {
  padding: 6px;
  border-radius: 4px;
  background-color: var(--neutral-100);
  color: var(--neutral-600);
  border: none;
  cursor: pointer;
  transition: var(--transition);
}

.action-buttons .btn-icon:hover {
  background-color: var(--primary-light);
  color: var(--primary);
}

.btn-cancel:hover {
  background-color: #fef2f2 !important;
  color: #b91c1c !important;
}

.payment-amount {
  font-weight: 500;
  color: var(--neutral-700);
}

/* Status indicators */
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

.status-accepted {
  background-color: #ecfdf5;
  color: #065f46;
  border-color: #a7f3d0;
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

/* Profile section styling */
.profile-section {
  background: #fff;
  padding: 0;
  overflow: hidden;
  border-radius: 12px;
  box-shadow: var(--card-shadow);
}

.profile-section .section-header {
  padding: 20px 24px;
  margin-bottom: 0;
  border-bottom: 1px solid var(--neutral-200);
}

.profile-card {
  padding: 0;
}

.profile-header {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background-color: var(--primary-light);
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
}

.profile-name {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--neutral-800);
}

.profile-info {
  padding: 24px;
}

.info-group {
  margin-bottom: 16px;
  border-bottom: 1px solid var(--neutral-200);
  padding-bottom: 16px;
}

.info-group:last-child {
  margin-bottom: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.info-label {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--neutral-500);
  margin: 0 0 4px 0;
}

.info-icon {
  margin-right: 8px;
}

.info-value {
  margin: 0;
  font-size: 16px;
  color: var(--neutral-800);
  font-weight: 500;
}

.medical-record {
  background-color: var(--neutral-100);
  padding: 12px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 14px;
  overflow-wrap: break-word;
}

/* Currency input styling */
.input-prefix {
  position: relative;
  width: 100%;
}

.currency-symbol {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--neutral-600);
  font-weight: 500;
}

.input-prefix input {
  padding-left: 28px;
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
  border: 2px solid var(--neutral-200);
  border-top: 2px solid var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-left: 8px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Message styling */
.message {
  margin-top: 20px;
  font-weight: 500;
  padding: 16px;
  border-radius: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message::before {
  content: '';
  display: inline-block;
  width: 20px;
  height: 20px;
  margin-right: 12px;
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
}

.success {
  background-color: #ecfdf5;
  color: #065f46;
  border-left: 4px solid #10b981;
}

.success::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%2310b981'%3E%3Cpath fill-rule='evenodd' d='M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' clip-rule='evenodd' /%3E%3C/svg%3E");
}

.error {
  background-color: #fef2f2;
  color: #b91c1c;
  border-left: 4px solid #ef4444;
}

.error::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%23ef4444'%3E%3Cpath fill-rule='evenodd' d='M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z' clip-rule='evenodd' /%3E%3C/svg%3E");
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

/* Form sections styling */
.form-section {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--neutral-200);
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.form-section-title {
  font-size: 16px;
  color: var(--neutral-700);
  margin-bottom: 16px;
  font-weight: 600;
}

.input-icon {
  margin-right: 6px;
  color: var(--neutral-500);
}

/* Nurse card */
.nurse-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: var(--primary-light);
  border-radius: 8px;
  margin-bottom: 16px;
}

.nurse-details {
  flex: 1;
}

.nurse-name {
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--neutral-800);
}

.nurse-availability {
  font-size: 14px;
  color: var(--neutral-600);
  margin: 0 0 8px 0;
}

.empty-nurse-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background-color: var(--neutral-100);
  border-radius: 8px;
  gap: 12px;
}

.empty-nurse-state p {
  margin: 0;
  color: var(--neutral-600);
}

/* Modal styling */
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

/* Media queries for responsive design */
@media (min-width: 768px) {
  .booking-container {
    grid-template-columns: 2fr 1fr;
  }

  .dashboard-header,
  .view-bookings {
    grid-column: 1 / -1; /* Span across all columns */
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

  .form-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .info-group {
    padding-bottom: 12px;
    margin-bottom: 12px;
  }

  .modal-content {
    max-height: 95vh;
  }
}
</style>