<template>
  <div class="booking-container">
    <h1>Booking Management</h1>

    <!-- Section: View All Bookings -->
    <section class="view-bookings">
      <h2>View All Bookings</h2>
      <button class="btn-refresh" @click="getBookings">Refresh Bookings</button>
      <table v-if="bookings.length">
        <thead>
          <tr>
            <th>BID</th>
            <th>PID</th>
            <th>NID</th>
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
            <td>{{ booking.fields.StartTime?.timestampValue }}</td>
            <td>{{ booking.fields.EndTime?.timestampValue }}</td>
            <td>{{ booking.fields.Status?.stringValue }}</td>
            <td>{{ booking.fields.Notes?.stringValue }}</td>
            <td>{{ booking.fields.PaymentAmt?.doubleValue }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else>
        No bookings available.
      </div>
    </section>

    <!-- Section: Create Booking -->
    <section class="create-booking">
      <h2>Create Booking</h2>
      <form @submit.prevent="createBooking">
        <div class="form-group">
          <label for="pid">Patient ID (PID):</label>
          <input
            type="text"
            id="pid"
            v-model="newBooking.PID"
            placeholder="Enter Patient ID"
            required
          />
        </div>
        <div class="form-group">
          <label for="nid">Nurse ID (NID):</label>
          <input
            type="text"
            id="nid"
            v-model="newBooking.NID"
            placeholder="Enter Nurse ID"
            required
          />
        </div>
        <div class="form-group">
          <label for="startTime">Start Time:</label>
          <!-- Use VueDatePicker for consistency -->
          <VueDatePicker
            v-model="newBooking.StartTime"
            :required="true"
            :enableTimePicker="true"
          />
        </div>
        <div class="form-group">
          <label for="endTime">End Time:</label>
          <VueDatePicker
            v-model="newBooking.EndTime"
            :required="true"
            :enableTimePicker="true"
          />
        </div>
        <div class="form-group">
          <label for="notes">Notes:</label>
          <textarea
            id="notes"
            v-model="newBooking.Notes"
            placeholder="Additional notes"
          ></textarea>
        </div>
        <div class="form-group">
          <label for="paymentAmt">Payment Amount:</label>
          <input
            type="number"
            step="0.01"
            id="paymentAmt"
            v-model="newBooking.PaymentAmt"
            placeholder="0.00"
            required
          />
        </div>
        <button type="submit" class="btn-submit">Create Booking</button>
      </form>
      <div v-if="createMessage" class="message">
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

        <button type="submit" class="btn-submit">Accept Booking</button>
      </form>
      <div v-if="acceptMessage" class="message">
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
      acceptMessage: ''
    }
  },
  methods: {
    getBookings() {
      axios
        .get('https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/GetAllBookings')
        .then(response => {
          this.bookings = response.data.Bookings || [];
        })
        .catch(error => {
          console.error("Error fetching bookings:", error);
        });
    },
    createBooking() {
      axios
        .post(
          'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingComposite/rest/v1/CreateBookingPatient',
          this.newBooking
        )
        .then(() => {
          this.createMessage = "Booking created successfully!";
          this.getBookings();
        })
        .catch(error => {
          console.error("Error creating booking:", error);
          this.createMessage = "Error creating booking.";
        });
    },
    acceptBooking() {
      axios
        .post(
          'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingComposite/rest/v1/AcceptBooking',
          this.acceptData
        )
        .then(() => {
          this.acceptMessage = "Booking accepted successfully!";
          this.getBookings();
        })
        .catch(error => {
          console.error("Error accepting booking:", error);
          this.acceptMessage = "Error accepting booking.";
        });
    }
  },
  created() {
    // Initial load of bookings
    this.getBookings();
  }
}
</script>

<style scoped>
.booking-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  padding: 20px;
  background: #fafafa;
}

.booking-container h1 {
  text-align: center;
  margin-bottom: 0;
}

section {
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #ddd;
  box-shadow: 0 2px 3px rgba(0,0,0,0.08);
}

section h2 {
  margin-top: 0;
  color: #444;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: inline-block;
  width: 160px;
  font-weight: bold;
}

input, textarea {
  padding: 6px 8px;
  width: 280px;
  font-size: 14px;
}

textarea {
  resize: vertical;
}

.btn-refresh,
.btn-submit {
  padding: 8px 14px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 14px;
  background-color: #007bff;
  color: #fff;
}

.btn-refresh:hover,
.btn-submit:hover {
  opacity: 0.8;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  background: #fff;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background-color: #f7f7f7;
}

.message {
  margin-top: 10px;
  font-weight: bold;
  padding: 8px;
  border-radius: 4px;
}

/* Simple success/error coloring example. If you want to differentiate messages,
   you could set successMessage or errorMessage in data and style accordingly. */

.message {
  background-color: #e7f7e7; /* light green background for success by default */
  color: #2e7d32;            /* dark green text */
}
</style>
