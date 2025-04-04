<template>
  <div class="booking-container">
    <h1>Booking Management</h1>

    <!-- Section: View All Bookings -->
    <section class="view-bookings">
      <div class="section-header">
        <h2>View All Bookings</h2>
        <button class="btn-refresh" @click="getBookings" :disabled="isLoadingBookings">
          <span v-if="isLoadingBookings">Loading...</span>
          <span v-else>Refresh Bookings</span>
        </button>
      </div>

      <div v-if="isLoadingBookings" class="loader-container">
        <div class="loader"></div>
        <p>Loading bookings...</p>
      </div>

      <div v-else-if="bookings.length === 0" class="empty-state">
        <p>No bookings available.</p>
      </div>

      <div v-else class="table-responsive">
        <table>
          <thead>
          <tr>
            <th>BID</th>
            <th>Patient</th>
            <th>Nurse</th>
            <th>Start Time</th>
            <th>End Time</th>
            <th>Status</th>
            <th>Notes</th>
            <th>Payment</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(booking, index) in bookings" :key="index">
            <td>{{ booking.fields.BID?.stringValue }}</td>
            <td>{{ booking.fields.PID?.stringValue }}</td>
            <td>{{ booking.fields.NID?.stringValue }}</td>
            <td>{{ formatDateTime(booking.fields.StartTime?.timestampValue) }}</td>
            <td>{{ formatDateTime(booking.fields.EndTime?.timestampValue) }}</td>
            <td>
                <span :class="getStatusClass(booking.fields.Status?.stringValue)">
                  {{ booking.fields.Status?.stringValue }}
                </span>
            </td>
            <td>{{ booking.fields.Notes?.stringValue || 'N/A' }}</td>
            <td>${{ booking.fields.PaymentAmt?.doubleValue }}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Section: Create Booking -->
    <section class="create-booking">
      <h2>Create Booking</h2>
      <form @submit.prevent="createBooking">
        <div class="form-group">
          <label for="pid">Patient Selection:</label>
          <div class="input-wrapper">
            <select
                id="pid"
                v-model="newBooking.PID"
                :disabled="isLoadingPatients"
                required
            >
              <option value="" disabled selected>Select a patient</option>
              <option v-for="patient in patients" :key="patient.PID" :value="patient.PID">
                {{ patient.Name }}
              </option>
            </select>
            <div v-if="isLoadingPatients" class="input-loader"></div>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="startTime">Start Time:</label>
            <VueDatePicker
                id="startTime"
                v-model="newBooking.StartTime"
                :required="true"
                :enableTimePicker="true"
                placeholder="Select start time"
            />
          </div>

          <div class="form-group">
            <label for="endTime">End Time:</label>
            <VueDatePicker
                id="endTime"
                v-model="newBooking.EndTime"
                :required="true"
                :enableTimePicker="true"
                placeholder="Select end time"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="nid">Nurse Selection:</label>
          <div class="input-wrapper">
            <select
                id="nid"
                v-model="newBooking.NID"
                :disabled="isLoadingNurses"
                required
            >
              <option value="" disabled selected>Select a nurse</option>
              <option v-for="nurse in nurses" :key="nurse.NID" :value="nurse.NID">
                {{ nurse.name }} - Available: {{ nurse.availableTiming }}
              </option>
            </select>
            <div v-if="isLoadingNurses" class="input-loader"></div>
          </div>
        </div>

        <div class="form-group">
          <label for="notes">Notes:</label>
          <div class="input-wrapper">
          <textarea
              id="notes"
              v-model="newBooking.Notes"
              placeholder="Additional notes"
              rows="3"
          ></textarea>
          </div>
        </div>

        <div class="form-group">
          <label for="paymentAmt">Payment Amount:</label>
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

        <div class="form-actions">
          <button type="submit" class="btn-submit" :disabled="isCreatingBooking">
            <span v-if="isCreatingBooking">Creating...</span>
            <span v-else>Create Booking</span>
          </button>
        </div>
      </form>

      <div v-if="createMessage" :class="['message', createSuccess ? 'success' : 'error']">
        {{ createMessage }}
      </div>
    </section>

    <!-- Section: Accept Booking -->
    <section class="accept-booking">
      <h2>Accept Booking</h2>
      <form @submit.prevent="acceptBooking">
        <div class="form-group">
          <label for="acceptBid">Booking ID (BID):</label>
          <input
              type="text"
              id="acceptBid"
              v-model="acceptData.bid"
              placeholder="Enter Booking ID"
              required
          />
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-submit" :disabled="isAcceptingBooking">
            <span v-if="isAcceptingBooking">Processing...</span>
            <span v-else>Accept Booking</span>
          </button>
        </div>
      </form>

      <div v-if="acceptMessage" :class="['message', acceptSuccess ? 'success' : 'error']">
        {{ acceptMessage }}
      </div>
    </section>
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
      bookings: [],
      nurses: [],
      patients: [],
      selectedNurse: null,

      // Loading states
      isLoadingBookings: false,
      isLoadingNurses: false,
      isLoadingPatients: false,
      isCreatingBooking: false,
      isAcceptingBooking: false,

      // Form data
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

      // Message states
      createMessage: '',
      createSuccess: false,
      acceptMessage: '',
      acceptSuccess: false
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

    getBookings() {
      this.isLoadingBookings = true;

      axios
          .get('https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/GetAllBookings')
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
            this.patients = response.data.Patients;
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

    acceptBooking() {
      this.isAcceptingBooking = true;
      this.acceptMessage = '';

      axios
          .post(
              'http://localhost:5008/v1/AcceptBooking',
              this.acceptData
          )
          .then(() => {
            this.acceptMessage = "Booking accepted successfully!";
            this.acceptSuccess = true;
            this.getBookings();

            // Reset form
            this.acceptData.bid = '';
          })
          .catch(error => {
            console.error("Error accepting booking:", error);
            this.acceptMessage = "Error accepting booking. Please try again.";
            this.acceptSuccess = false;
          })
          .finally(() => {
            this.isAcceptingBooking = false;
          });
    }
  },
  created() {
    // Initial load of data with loading states
    this.getBookings();
    this.getAllPatients();
    this.getAllNurses();
  },
}
</script>

<style scoped>
.booking-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  padding: 24px;
  background: #f5f7fa;
  max-width: 1200px;
  margin: 0 auto;
}

.booking-container h1 {
  text-align: center;
  margin-bottom: 0;
  color: #2c3e50;
  font-size: 28px;
}

section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e1e4e8;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

section h2 {
  margin-top: 0;
  color: #2c3e50;
  font-size: 20px;
  margin-bottom: 20px;
  border-bottom: 1px solid #eaeaea;
  padding-bottom: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  margin: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #4a5568;
}

input, textarea, select {
  padding: 10px 12px;
  width: 100%;
  font-size: 14px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  transition: border-color 0.2s;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

textarea {
  resize: vertical;
  min-height: 80px;
}

.btn-refresh,
.btn-submit {
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  background-color: #3498db;
  color: #fff;
  transition: all 0.2s;
}

.btn-refresh:hover,
.btn-submit:hover {
  background-color: #2980b9;
}

.btn-refresh:disabled,
.btn-submit:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.form-actions {
  margin-top: 20px;
}

/* Table styles */
.table-responsive {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  background: #fff;
  font-size: 14px;
}

th, td {
  border: 1px solid #e2e8f0;
  padding: 12px;
  text-align: left;
}

th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #4a5568;
}

tr:nth-child(even) {
  background-color: #f9fafb;
}

tr:hover {
  background-color: #f1f5f9;
}

/* Message styles */
.message {
  margin-top: 16px;
  font-weight: 500;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
}

.success {
  background-color: #e6f7ee;
  color: #0d5f3a;
  border-left: 4px solid #0d5f3a;
}

.error {
  background-color: #fee2e2;
  color: #b91c1c;
  border-left: 4px solid #b91c1c;
}

/* Loading indicators */
.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
}

.loader {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

.input-wrapper {
  position: relative;
}

.input-loader {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Empty state */
.empty-state {
  padding: 32px;
  text-align: center;
  color: #64748b;
  font-style: italic;
}

/* Status colors */
.status-pending {
  background-color: #fef3c7;
  color: #92400e;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-accepted {
  background-color: #e0f2fe;
  color: #0c4a6e;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-completed {
  background-color: #dcfce7;
  color: #166534;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-cancelled {
  background-color: #fee2e2;
  color: #991b1b;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

/* Currency input styling */
.input-prefix {
  position: relative;
}

.currency-symbol {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
}

.input-prefix input {
  padding-left: 24px;
}

/* Media queries for responsive design */
@media (min-width: 768px) {
  .booking-container {
    grid-template-columns: 1fr 1fr;
  }

  .view-bookings {
    grid-column: 1 / -1; /* Span across all columns */
  }
}

@media (max-width: 767px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>