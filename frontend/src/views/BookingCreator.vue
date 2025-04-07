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
        <div class="time-restrictions-info">
          <div class="info-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <div class="info-content">
            <h4>Booking Time Restrictions</h4>
            <ul>
              <li>Appointments must be booked at least 24 hours in advance</li>
              <li>Available hours: 9:00 AM - 11:00 PM</li>
              <li>All appointments must end by 11:00 PM</li>
            </ul>
          </div>
        </div>
        <div class="form-section">
          <h3 class="form-section-title">1. Choose Date & Time</h3>

            <!-- Calendar now gets its own row -->
            <div class="form-group" style="margin-left: auto; margin-right: auto">
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
                  inline
                  auto-apply
                  :disabled="isLoadingBookings"
                  :enable-minutes="false"
                  id="startTime"
                  :is24="true"
                  v-model="newBooking.StartTime"
                  :minutes-increment="5"
                  :required="true"
                  :enableTimePicker="true"
                  :clearable="false"
                  :min-date="minBookingDate"
                  :min-time="minTimeLimit"
                  :max-time="maxTimeLimit"
                  :disabled-dates="getBookedDates()"
                  :highlight-dates="getBookedDates()"
                  :day-class="getDayClass"
                  placeholder="Select start time"
                  class="date-picker"
                  @update:modelValue="calculateEndTimeAndPayment"
              />
              <div v-if="validationErrors.startTime" class="validation-error">
                {{ validationErrors.startTime }}
              </div>
            </div>

            <!-- Duration slider now gets its own row -->
          <div class="form-group">
            <label for="durationHours">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="input-icon">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              Duration (Hours)
            </label>
            <div class="slider-container">
              <input
                  type="range"
                  id="durationHours"
                  v-model="durationHours"
                  min="1"
                  :max="maxAllowedDuration"
                  step="1"
                  class="duration-slider"
                  @input="calculateEndTimeAndPayment"
              >
              <div class="duration-display">{{ durationHours }} {{ durationHours === 1 ? 'hour' : 'hours' }}</div>
            </div>
          </div>

            <div class="duration-summary" v-if="newBooking.StartTime && newBooking.EndTime">
              <div class="summary-row">
                <span class="summary-label">Appointment Period:</span>
                <span class="summary-value">{{ formatTime(newBooking.StartTime) }} - {{ formatTime(newBooking.EndTime) }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">Date:</span>
                <span class="summary-value">{{ formatDate(newBooking.StartTime) }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">Total Duration:</span>
                <span class="summary-value">{{ durationHours }} {{ durationHours === 1 ? 'hour' : 'hours' }}</span>
              </div>
              <div class="summary-row pricing-row">
                <span class="summary-label">Calculated Price:</span>
                <span class="summary-value price-value">${{ calculatedPrice.toFixed(2) }}</span>
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
              Notes and Requirements <span class="required-label">*</span>
            </label>
            <textarea
                id="notes"
                v-model="newBooking.Notes"
                placeholder="Describe your needs or any special requirements for this appointment"
                rows="3"
            ></textarea>
            <div v-if="validationErrors.notes" class="validation-error">
              {{ validationErrors.notes }}
            </div>
          </div>

          <div class="price-display">
            <div class="price-info">
              <div class="price-label">Calculated Payment:</div>
              <div class="price-value">${{ calculatedPrice.toFixed(2) }}</div>
            </div>
            <div class="price-details">
              <div class="price-breakdown">
                <div class="breakdown-item">
                  <span>Base rate (1 hour):</span>
                  <span>${{ baseRate.toFixed(2) }}</span>
                </div>
                <div class="breakdown-item" v-if="durationHours > 1">
                  <span>Additional hours ({{ durationHours - 1 }}):</span>
                  <span>${{ (calculatedPrice - baseRate).toFixed(2) }}</span>
                </div>
                <div class="breakdown-item total">
                  <span>Total amount:</span>
                  <span>${{ calculatedPrice.toFixed(2) }}</span>
                </div>
              </div>
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
<!--        <button class="btn-text">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
          Edit Profile
        </button>-->
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
      </div>
    </div>
    <div v-if="isProcessingPayment" class="payment-overlay">
      <div class="payment-status-card">
        <div class="payment-status-icon" :class="{ 'success': createSuccess, 'error': !createSuccess && createMessage.includes('cancelled') }">
          <div v-if="!createSuccess && !createMessage.includes('cancelled')" class="payment-loader"></div>
          <svg v-else-if="createSuccess" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        </div>

        <h3 class="payment-status-title">
          {{ getPaymentStatusTitle() }}
        </h3>

        <p class="payment-status-message">{{ createMessage }}</p>

        <div class="payment-status-steps">
          <div class="payment-step" :class="{ 'active': paymentStep >= 1, 'completed': paymentStep > 1 }">
            <div class="step-indicator">1</div>
            <div class="step-label">Creating payment</div>
          </div>
          <div class="step-connector"></div>
          <div class="payment-step" :class="{ 'active': paymentStep >= 2, 'completed': paymentStep > 2 }">
            <div class="step-indicator">2</div>
            <div class="step-label">Processing payment</div>
          </div>
          <div class="step-connector"></div>
          <div class="payment-step" :class="{ 'active': paymentStep >= 3, 'completed': paymentStep > 3 }">
            <div class="step-indicator">3</div>
            <div class="step-label">Confirming booking</div>
          </div>
        </div>

        <button v-if="createMessage.includes('cancelled') || (createMessage.includes('closed') && !createSuccess)"
                class="btn-retry"
                @click="retryPayment">
          Try Again
        </button>
      </div>
    </div>
    <div class="toast-container">
      <transition-group name="toast">
        <div v-for="(toast, index) in toastMessages" :key="toast.id"
             class="toast-notification"
             :class="toast.type">
          <div class="toast-icon">
            <svg v-if="toast.type === 'success'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <svg v-else-if="toast.type === 'error'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </div>
          <div class="toast-content">
            <p>{{ toast.message }}</p>
          </div>
          <button class="toast-close" @click="removeToast(index)">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </transition-group>
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
      isProcessingPayment: false,
      paymentSessionId: null,
      tempBookingId: null,
      paymentWindow: null,
      paymentCheckInterval: null,
      paymentStep: 1, // Track the current step in the payment process
      toastMessages: [], // Array to store toast notifications
      toastCounter: 0, // Counter for unique toast IDs

      minTimeLimit: { hours: 9, minutes: 0 },  // 9:00 AM
      maxTimeLimit: { hours: 23, minutes: 0 }, // 11:00 PM

      // New fields for duration-based booking
      durationHours: 1,
      baseRate: 20, // Base rate for 1 hour in dollars
      calculatedPrice: 20, // Initial calculated price

      validationErrors: {
        startTime: '',
        notes: '',
        nurse: ''
      },

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
    findNextAvailableDay() {
      // Start with tomorrow, ya get me?
      let candidateDate = new Date();
      candidateDate.setDate(candidateDate.getDate() + 1);
      candidateDate.setHours(9, 0, 0, 0); // 9 AM sharp, innit

      // We ain't checkin' more than 30 days, fuck that
      const MAX_DAYS_TO_CHECK = 30;

      // Loop through the next 30 days, ya get me?
      for (let i = 0; i < MAX_DAYS_TO_CHECK; i++) {
        // Check if this day's got bookings
        const isBooked = this.bookings.some(booking => {
          const bookingDate = new Date(booking.fields.StartTime?.timestampValue);
          return (
              bookingDate.getFullYear() === candidateDate.getFullYear() &&
              bookingDate.getMonth() === candidateDate.getMonth() &&
              bookingDate.getDate() === candidateDate.getDate()
          );
        });

        // If it ain't booked, we found our fuckin' day!
        if (!isBooked) {
          return candidateDate;
        }

        // Move to the next day, ya slag
        candidateDate.setDate(candidateDate.getDate() + 1);
      }

      // If everyfink's booked, just use tomorrow, fuck it
      let tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(9, 0, 0, 0);
      return tomorrow;
    },
    validateForm() {
      // Reset validation errors
      this.validationErrors = {
        startTime: '',
        notes: '',
        nurse: ''
      };

      let isValid = true;

      // Validate start time
      if (!this.newBooking.StartTime) {
        this.validationErrors.startTime = 'Please select a start time for your appointment';
        isValid = false;
      } else {
        // Check if start time is in the past
        const now = new Date();
        const startTime = new Date(this.newBooking.StartTime);

        if (startTime < now) {
          this.validationErrors.startTime = 'You cannot book appointments in the past';
          isValid = false;
        }

        // Check if booking is within 24 hours
        const minDate = new Date();
        minDate.setHours(minDate.getHours() + 24);
        if (startTime < minDate) {
          this.validationErrors.startTime = 'Appointments must be booked at least 24 hours in advance';
          isValid = false;
        }

        // Check time restrictions (9 AM - 11 PM)
        const hours = startTime.getHours();
        if (hours < this.minTimeLimit.hours || hours >= this.maxTimeLimit.hours) {
          this.validationErrors.startTime = 'Appointment hours are limited to between 9 AM and 11 PM';
          isValid = false;
        }

        // Check end time
        if (this.newBooking.EndTime) {
          const endTime = new Date(this.newBooking.EndTime);
          const endHours = endTime.getHours();

          if (endHours >= this.maxTimeLimit.hours && endTime.getMinutes() > 0) {
            this.validationErrors.startTime = 'Appointments cannot end after 11 PM';
            isValid = false;
          }
        }
      }

      // Validate notes
      if (!this.newBooking.Notes || this.newBooking.Notes.trim() === '') {
        this.validationErrors.notes = 'Please provide details about your appointment requirements';
        isValid = false;
      }

      // Validate nurse assignment
      if (!this.selectedNurse || !this.selectedNurse.NID) {
        this.validationErrors.nurse = 'A nurse must be assigned to your appointment';
        isValid = false;
      }

      return isValid;
    },
    showTimeRestrictionInfo() {
      this.showToast(
          'Reminder: Appointments can only be booked between 9 AM and 11 PM, and must be scheduled at least 24 hours in advance.',
          'info',
          8000
      );
    },
    // Calculate end time based on start time and duration hours
    calculateEndTimeAndPayment() {
      if (!this.newBooking.StartTime) return;

      // Ensure duration doesn't exceed maximum allowed
      this.durationHours = Math.min(this.durationHours, this.maxAllowedDuration);

      // Create a new date object for end time by adding hours to start time
      const startTime = new Date(this.newBooking.StartTime);
      const endTime = new Date(startTime);
      endTime.setHours(startTime.getHours() + parseInt(this.durationHours));

      // Check if end time exceeds 11 PM
      const endHour = endTime.getHours();
      if (endHour >= this.maxTimeLimit.hours || (endHour === 0 && endTime.getDate() > startTime.getDate())) {
        // If it does, adjust duration to end at 11 PM
        endTime.setHours(this.maxTimeLimit.hours);
        endTime.setMinutes(0);

        // Recalculate duration
        const diffHours = (endTime - startTime) / (1000 * 60 * 60);
        this.durationHours = Math.max(1, Math.floor(diffHours));
      }

      // Update the end time
      this.newBooking.EndTime = endTime;

      // Calculate the payment based on exponential pricing formula
      this.calculatePayment();
    },

    // Exponential pricing calculation
    calculatePayment() {
      // Base rate for first hour
      let total = this.baseRate;

      // For additional hours, apply exponential pricing
      // Formula: base_rate + (hour_number^1.5 * factor)
      if (this.durationHours > 1) {
        for (let hour = 2; hour <= this.durationHours; hour++) {
          // Exponential factor makes each additional hour more expensive
          //const hourFactor = Math.pow(hour, 2.5);
          const hourFactor = 8.5
          total += (this.baseRate / 2) * (hourFactor / 5);
        }
      }

      // Update the calculated price and payment amount
      this.calculatedPrice = Math.round(total * 100) / 100; // Round to 2 decimal places
      this.newBooking.PaymentAmt = this.calculatedPrice;
    },

    showToast(message, type = 'info', duration = 5000) {
      const toast = {
        id: this.toastCounter++,
        message,
        type
      };

      this.toastMessages.push(toast);

      // Auto remove toast after duration
      if (duration > 0) {
        setTimeout(() => {
          this.removeToast(this.toastMessages.findIndex(t => t.id === toast.id));
        }, duration);
      }

      return toast.id;
    },

    // Remove a toast notification
    removeToast(index) {
      if (index > -1) {
        this.toastMessages.splice(index, 1);
      }
    },

    // Get the title for the payment status card based on current state
    getPaymentStatusTitle() {
      if (this.createSuccess) {
        return 'Payment Successful';
      } else if (this.createMessage.includes('cancelled')) {
        return 'Payment Cancelled';
      } else if (this.createMessage.includes('closed')) {
        return 'Payment Window Closed';
      } else {
        return 'Processing Payment';
      }
    },

    // Retry payment
    retryPayment() {
      this.resetPaymentState(); // Add this line
      this.createMessage = '';
      this.createStripePayment();
    },
    createStripePayment() {
      this.prepareForNewPayment();

      // NOW set the overlay state
      this.isProcessingPayment = true;
      this.paymentStep = 1;
      this.createMessage = "Setting up your secure payment...";

      // Generate a COMPLETELY NEW BOOKING ID EVERY FUCKIN' TIME
      this.tempBookingId = 'BID-' + Math.random().toString(36).substring(2, 11).toUpperCase();

      const paymentData = {
        amount: this.calculatedPrice,
        booking_id: this.tempBookingId,
        patient_id: this.selectedPatient.PID,
        nurse_id: this.selectedNurse.NID
      };

      axios.post('http://localhost:5010/create-payment-link', paymentData)
          .then(response => {
            if (response.data.success) {
              this.paymentSessionId = response.data.session_id;
              this.paymentStep = 2;
              this.createMessage = "Payment window opened. Please complete your payment.";

              // Open payment in a BRAND FUCKIN' NEW window using vanilla JS
              const width = 550;
              const height = 650;
              const left = (window.screen.width / 2) - (width / 2);
              const top = (window.screen.height / 2) - (height / 2);

              try {
                // Open window WITHOUT assigning it yet
                const newWindow = window.open(
                    response.data.payment_url,
                    'stripe_checkout_' + new Date().getTime(), // UNIQUE NAME EVERY TIME
                    `width=${width},height=${height},top=${top},left=${left},toolbar=no,location=no,status=no,menubar=no`
                );

                // NOW assign it to vue property on next tick
                this.$nextTick(() => {
                  this.paymentWindow = newWindow;
                });

                // Add message listener AFTER window creation
                window.addEventListener('message', this.handlePaymentMessage);

                // Set interval to check window status
                this.paymentCheckInterval = setInterval(() => {
                  try {
                    // Add this check first - if we're already successful, don't check the window
                    if (this.createSuccess || this.paymentStep >= 3) {
                      console.log("Payment successful, stopping window checks");
                      clearInterval(this.paymentCheckInterval);
                      return;
                    }

                    if (this.paymentWindow && this.paymentWindow.closed) {
                      console.log("Window detected as closed");
                      this.onPaymentWindowClosed();
                    }
                  } catch (e) {
                    // If we can't check, don't assume anything
                    console.log("Can't check window state:", e);
                  }
                }, 1000); // Give it a full fuckin' second between checks

              } catch (error) {
                console.error("Error opening payment window:", error);
                this.createMessage = "Couldn't open payment window. Please try again.";
                this.createSuccess = false;
                this.resetPaymentState();
              }
            } else {
              this.createMessage = "Error creating payment link. Please try again.";
              this.createSuccess = false;
              this.isProcessingPayment = false;
              this.isCreatingBooking = false;
              this.showToast("Failed to create payment link. Please try again.", "error");
            }
          })
          .catch(error => {
            console.error("Error creating Stripe payment:", error);
            this.createMessage = "Payment service error. Please try again.";
            this.createSuccess = false;
            this.isProcessingPayment = false;
            this.isCreatingBooking = false;
            this.showToast("Payment service error. Please try again later.", "error");
          });
    },
    handlePaymentMessage(event) {
      // Ignore messages from unknown sources
      if (!event.data || !event.data.type) return;

      // Handle payment completion
      if (event.data.type === 'PAYMENT_COMPLETED') {
        // Clean up listeners but keep the payment state
        window.removeEventListener('message', this.handlePaymentMessage);
        if (this.paymentCheckInterval) {
          clearInterval(this.paymentCheckInterval);
        }

        // Set session ID and process payment
        this.paymentSessionId = event.data.sessionId;
        this.createMessage = "Payment successful! Verifying...";
        this.createSuccess = true;
        this.paymentStep = 3; // Move to third step

        // Check payment status
        this.checkPaymentStatus();
      }

      // Handle payment cancellation
      if (event.data.type === 'PAYMENT_CANCELLED') {
        this.createMessage = "Payment was cancelled. Please try again.";
        this.createSuccess = false;
        this.resetPaymentState(); // Use our new function
        this.showToast("Payment was cancelled. You can try again when ready.", "info");
      }
    },
    onPaymentWindowClosed() {
      // DON'T RESET FUCK ALL if we're already successful or in step 3
      if (this.createSuccess || this.paymentStep >= 3) {
        console.log("Window closed but payment in progress - NOT resetting state");
        return; // JUST FUCKIN' BAIL OUT - don't touch nuffink
      }

      // Only if we're still in early steps and not successful, then we clean up
      console.log("Window closed before payment completed - cleaning up");
      this.resetPaymentState();
      this.createMessage = "Payment window closed. Please try again if your payment wasn't completed.";
      this.showToast("Payment window closed. No payment was processed.", "info");
    },
    checkPaymentStatus() {
      if (!this.paymentSessionId) {
        this.resetPaymentState();
        return;
      }

      this.createMessage = "Verifying payment status...";

      axios.get(`http://localhost:5010/payment-status/${this.paymentSessionId}`)
          .then(response => {
            if (response.data.success && response.data.payment_status === 'paid') {
              // Payment succeeded, finalize the booking
              this.createSuccess = true;
              this.createMessage = "Payment successful! Creating your booking...";
              this.finalizeBooking();
            } else {
              // Payment not successful or still pending
              this.createMessage = "Payment not completed. Please try again.";
              this.createSuccess = false;
              this.resetPaymentState(); // Add this line
              this.showToast("Payment verification failed. Please try again.", "error");
            }
          })
          .catch(error => {
            console.error("Error checking payment status:", error);
            this.createMessage = "Error verifying payment. Please contact support.";
            this.createSuccess = false;
            this.resetPaymentState(); // Add this line
            this.showToast("Error verifying payment. Please contact support.", "error");
          });
    },
    finalizeBooking() {
      // Set the booking ID from our temp ID
      this.newBooking.BID = this.tempBookingId;

      axios.post(
          'http://localhost:5008/v1/MakeBooking',
          this.newBooking
      )
          .then(() => {
            this.paymentStep = 4; // Complete all steps
            this.createMessage = "Success! Your appointment has been booked and payment confirmed.";
            this.createSuccess = true;

            // Use our new function instead
            this.cleanupAfterSuccessfulPayment();

            // Show toast and update UI
            this.showToast("Your appointment has been successfully booked!", "success");
            this.getBookings();

            // Wait a bit before clearing the overlay
            setTimeout(() => {
              this.isProcessingPayment = false;
              this.resetForm();
            }, 2000);  // Give 'em 2 seconds to see the success message
          })
          .catch(error => {
            console.error("Error creating booking:", error);
            this.createMessage = "Payment was successful but there was an error creating the booking. Please contact support with reference: " + this.paymentSessionId;
            this.createSuccess = false;
            this.showToast("Error creating booking. Please contact support.", "error");
            this.resetPaymentState(); // This is fine for errors
          });
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
        StartTime: this.findNextAvailableDay(),
        EndTime: '',
        APIKey: '',
        Notes: '',
        PaymentAmt: 0
      };
      this.durationHours = 1;
      this.calculatedPrice = this.baseRate;
      this.randomNurse();
    },

    closePaymentWindowSafely() {
      try {
        const win = this.paymentWindow;
        this.paymentWindow = null;

        if (win && !win.closed) {
          win.close();
        }
      } catch (e) {
        console.log("Window's giving us grief:", e);
      }
    },

    prepareForNewPayment() {
      // Close any existing windows WITHOUT changing overlay state
      this.closePaymentWindowSafely();

      // Remove existing listeners
      window.removeEventListener('message', this.handlePaymentMessage);

      // Clear intervals
      if (this.paymentCheckInterval) {
        clearInterval(this.paymentCheckInterval);
        this.paymentCheckInterval = null;
      }

      // Fresh booking ID every time
      this.tempBookingId = 'BID-' + Math.random().toString(36).substring(2, 11).toUpperCase();
    },

    resetPaymentState() {
      // Close window first
      this.closePaymentWindowSafely();

      // THEN set overlay gone
      this.isProcessingPayment = false;

      // Clean up all listeners
      window.removeEventListener('message', this.handlePaymentMessage);
      if (this.paymentCheckInterval) {
        clearInterval(this.paymentCheckInterval);
        this.paymentCheckInterval = null;
      }

      // Reset everything else
      this.tempBookingId = null;
      this.paymentSessionId = null;
      this.isCreatingBooking = false;
      this.paymentStep = 1;
      this.createSuccess = false;
      this.createMessage = '';
    },
    // ADD THIS NEW FUNCTION
    cleanupAfterSuccessfulPayment() {
      // Just close window and clean up listeners - DON'T TOUCH THE OVERLAY
      this.closePaymentWindowSafely();
      window.removeEventListener('message', this.handlePaymentMessage);
      if (this.paymentCheckInterval) {
        clearInterval(this.paymentCheckInterval);
        this.paymentCheckInterval = null;
      }

      // Clear just these bits, NOT the overlay state
      this.tempBookingId = null;
      this.paymentSessionId = null;
      this.isCreatingBooking = false;

      console.log("Cleaned up payment resources but kept overlay VISIBLE");
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

            // RIGHT 'ERE! Set the next available day after we've got the bookings
            this.newBooking.StartTime = this.findNextAvailableDay();
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

    mounted() {
      // Show time restriction info after component is mounted
      this.$nextTick(() => {
        this.showTimeRestrictionInfo();
      });
    },

    createBooking() {
      this.resetPaymentState();
      // Validate the form first
      if (!this.validateForm()) {
        this.showToast('Please fill in all required fields', 'error');
        return;
      }

      this.isCreatingBooking = true;
      this.createMessage = '';

      // Set the patient and nurse IDs
      this.newBooking.PID = this.selectedPatient.PID;
      this.newBooking.NID = this.selectedNurse.NID;

      // Ensure end time is set correctly
      this.calculateEndTimeAndPayment();

      // Start the payment flow
      this.createStripePayment();
    },
    randomNurse() {
      if (true) {
        var ranNum = Math.floor(Math.random() * (this?.nurses?.length - 1 + 1))
        this.newBooking.NID = this?.nurses[ranNum]?.NID;
        this.selectedNurse = this?.nurses[ranNum];
      }
    },
    getBookedDates() {
      // This'll be a fackin' array of all yer booked dates, ya get me?
      return this.bookings.map(booking => {
        const startTime = new Date(booking.fields.StartTime?.timestampValue);
        return new Date(startTime.getFullYear(), startTime.getMonth(), startTime.getDate());
      });
    },
    getDayClass(day) {
      // Check if the day 'as a fackin' booking on it
      const date = new Date(day.year, day.month - 1, day.day);
      const isBooked = this.getBookedDates().some(bookedDate =>
          bookedDate.getFullYear() === date.getFullYear() &&
          bookedDate.getMonth() === date.getMonth() &&
          bookedDate.getDate() === date.getDate()
      );

      // Return yer custom CSS class if it's booked
      return isBooked ? 'booked-date' : '';
    }
  },
  watch: {
    'newBooking.StartTime': function(newTime) {
      if (newTime) {
        this.calculateEndTimeAndPayment();
      }
    }
  },
  created() {
    // Check for URL parameters that might indicate return from payment
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const status = urlParams.get('status');
    const isRedirect = urlParams.get('redirect') === 'true';

    // Only process params if it's not a redirect (redirects are handled by the interval)
    // This handles the case of a full page reload/direct URL access
    if (sessionId && status === 'success' && !isRedirect) {
      // Store the session ID and check payment status
      this.paymentSessionId = sessionId;
      this.tempBookingId = urlParams.get('booking_id');
      this.isProcessingPayment = true;

      // Remove params from URL
      window.history.replaceState({}, document.title, window.location.pathname);

      // Wait for component to fully initialize
      this.$nextTick(() => {
        this.checkPaymentStatus();
      });
    } else if (status === 'cancelled' && !isRedirect) {
      this.createMessage = "Payment was cancelled. Please try again.";
      this.createSuccess = false;
      this.isProcessingPayment = false;

      // Remove params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Initialize with calculated price
    this.calculatedPrice = this.baseRate;

    // Existing initialization code
    this.getCurrentPatient();
    this.getAllNurses();
  },
  computed: {
    minBookingDate() {
      const minDate = new Date();
      minDate.setHours(minDate.getHours() + 24); // Add 24 hours to current time
      return minDate;
    },
    maxAllowedDuration() {
      if (!this.newBooking.StartTime) return 12; // Default max

      const startDate = new Date(this.newBooking.StartTime);
      const startHour = startDate.getHours();

      // Calculate how many hours until 11 PM
      const hoursUntilClose = this.maxTimeLimit.hours - startHour;

      // If less than 1 hour until closing, show at least 1 hour
      return Math.max(1, hoursUntilClose);
    },
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

#startTime {
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.required-label {
  color: #ef4444;
  margin-left: 2px;
}

.validation-error {
  color: #ef4444;
  font-size: 14px;
  margin-top: 6px;
  font-weight: 500;
}

/* Style for the nurse section to display validation error */
.nurse-card {
  position: relative;
}

.nurse-validation-error {
  color: #ef4444;
  font-size: 14px;
  margin-top: 6px;
  font-weight: 500;
  position: absolute;
  bottom: -22px;
  left: 16px;
}

/* New Duration Slider Styles */
.slider-container {
  width: 100%;
  margin-bottom: 8px;
}

.duration-slider {
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--neutral-200);
  border-radius: 4px;
  outline: none;
  margin-top: 10px;
  margin-bottom: 16px;
}

.duration-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--primary);
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.duration-slider::-webkit-slider-thumb:hover {
  background: var(--secondary);
  transform: scale(1.1);
}

.duration-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--primary);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.duration-slider::-moz-range-thumb:hover {
  background: var(--secondary);
  transform: scale(1.1);
}

.duration-display {
  text-align: center;
  font-weight: 600;
  color: var(--primary);
  font-size: 16px;
  margin-top: -8px;
}

/* Duration Summary Styles */
.duration-summary {
  background-color: var(--primary-light);
  padding: 16px;
  border-radius: 8px;
  margin-top: 24px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.summary-row:last-child {
  margin-bottom: 0;
}

.summary-label {
  font-weight: 500;
  color: var(--neutral-700);
}

.summary-value {
  font-weight: 600;
  color: var(--neutral-800);
}

.pricing-row {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--neutral-300);
}

.price-value {
  color: var(--primary);
  font-size: 18px;
}

/* Price Display Styles */
.price-display {
  background-color: var(--primary-light);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.price-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.price-label {
  font-weight: 600;
  color: var(--neutral-700);
  font-size: 16px;
}

.price-value {
  font-weight: 700;
  color: var(--primary);
  font-size: 24px;
}

.price-details {
  padding-top: 12px;
  border-top: 1px dashed var(--neutral-300);
}

.price-breakdown {
  font-size: 14px;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  color: var(--neutral-600);
}

.breakdown-item.total {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--neutral-300);
  font-weight: 600;
  color: var(--neutral-800);
}

/* Existing Styles Below */
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
.payment-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(17, 24, 39, 0.85);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(3px);
}

.payment-status-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  width: 100%;
  max-width: 500px;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: cardAppear 0.3s ease-out;
}

@keyframes cardAppear {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.payment-status-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px auto;
}

.payment-status-icon.success {
  background-color: #ecfdf5;
  color: #10b981;
}

.payment-status-icon.error {
  background-color: #fef2f2;
  color: #ef4444;
}

.payment-loader {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 1s linear infinite;
}

.payment-status-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--neutral-800);
}

.payment-status-message {
  color: var(--neutral-600);
  margin-bottom: 24px;
  font-size: 15px;
  line-height: 1.5;
}

.payment-status-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.payment-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 80px;
}

.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--neutral-200);
  color: var(--neutral-600);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.step-label {
  font-size: 12px;
  color: var(--neutral-500);
  text-align: center;
  transition: all 0.3s ease;
}

.step-connector {
  flex-grow: 1;
  height: 2px;
  background-color: var(--neutral-200);
  position: relative;
  top: -14px;
  margin: 0 4px;
  transition: all 0.3s ease;
}

.payment-step.active .step-indicator {
  background-color: var(--primary);
  color: white;
}

.payment-step.active .step-label {
  color: var(--primary);
  font-weight: 500;
}

.payment-step.completed .step-indicator {
  background-color: #10b981;
  color: white;
}

.payment-step.completed .step-label {
  color: #10b981;
  font-weight: 500;
}

.payment-step.completed + .step-connector,
.payment-step.active + .step-connector {
  background-color: var(--primary);
}

.payment-step.completed + .step-connector {
  background-color: #10b981;
}

.btn-retry {
  padding: 12px 24px;
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(67, 97, 238, 0.1), 0 2px 4px -1px rgba(67, 97, 238, 0.06);
}

.btn-retry:hover {
  background-color: var(--secondary);
  transform: translateY(-1px);
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 1100;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 360px;
}

.toast-notification {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  animation: slideIn 0.3s ease-out;
  transition: all 0.3s ease;
  max-width: 360px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(40px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.toast-notification.success {
  background-color: #ecfdf5;
  border-left: 4px solid #10b981;
}

.toast-notification.error {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
}

.toast-notification.info {
  background-color: #eff6ff;
  border-left: 4px solid #3b82f6;
}

.toast-icon {
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-notification.success .toast-icon {
  color: #10b981;
}

.toast-notification.error .toast-icon {
  color: #ef4444;
}

.toast-notification.info .toast-icon {
  color: #3b82f6;
}

.toast-content {
  flex: 1;
}

.toast-content p {
  margin: 0;
  color: var(--neutral-800);
  font-size: 14px;
  line-height: 1.5;
}

.toast-close {
  background: none;
  border: none;
  color: var(--neutral-500);
  padding: 4px;
  margin-left: 12px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.toast-close:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--neutral-800);
}

/* Toast transition animations */
.toast-enter-active, .toast-leave-active {
  transition: all 0.3s;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
.time-restrictions-info {
  display: flex;
  background-color: #eff6ff; /* Light blue background */
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border-left: 4px solid #3b82f6; /* Blue accent */
}

.info-icon {
  color: #3b82f6;
  margin-right: 12px;
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
}

.info-content {
  flex: 1;
}

.info-content h4 {
  margin: 0 0 8px 0;
  color: #1e40af;
  font-size: 15px;
}

.info-content ul {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  font-size: 14px;
}

.info-content li {
  margin-bottom: 4px;
}

.info-content li:last-child {
  margin-bottom: 0;
}
.booked-date {
  background-color: #fef2f2 !important; /* Light red background */
  color: #b91c1c !important;
  border: 1px solid #fecaca !important;
  position: relative;
}

.booked-date::after {
  content: "🔒";
  position: absolute;
  bottom: 2px;
  right: 2px;
  font-size: 8px;
}
</style>
