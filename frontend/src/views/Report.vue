<template>
  <div class="reports-container">
    <div class="header">
      <h1>Nurse Reports</h1>
      <button @click="showGenerateModal = true" class="generate-btn">
        <PlusIcon class="icon" />
        Generate Monthly Report
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <LoaderIcon class="spin" />
      <p>Loading reports...</p>
    </div>

    <!-- Error state -->
    <div v-if="error" class="error-message">
      <AlertCircleIcon class="icon" />
      <p>{{ error }}</p>
    </div>

    <!-- Reports list -->
    <div v-if="!loading && !error && reports.length === 0" class="empty-state">
      <FileIcon class="icon" />
      <p>No reports available</p>
      <button @click="showGenerateModal = true" class="generate-btn">Generate your first report</button>
    </div>

    <div v-if="!loading && reports.length > 0" class="reports-list">
      <div v-for="report in reports" :key="report.id" class="report-card" @click="viewReport(report)">
        <div class="report-icon">
          <FileTextIcon />
        </div>
        <div class="report-details">
          <h3>{{ formatMonth(report.reportMonth) }}</h3>
          <div class="report-stats">
            <span>
              <ClockIcon class="mini-icon" /> {{ report.hoursWorked?.toFixed(1) || 'N/A' }} hours
            </span>
            <span>
              <CalendarIcon class="mini-icon" /> {{ report.totalBookings || 0 }} bookings
            </span>
          </div>
          <div class="report-date">Generated: {{ formatDate(report.createdAt) }}</div>
        </div>
      </div>
    </div>

    <!-- Report detail modal -->
    <div v-if="selectedReport" class="modal-overlay" @click="selectedReport = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ formatMonth(selectedReport.reportMonth) }} Report</h2>
          <button class="close-btn" @click="selectedReport = null">
            <XIcon />
          </button>
        </div>
        <div class="modal-body" v-html="reportContent"></div>
        <div class="modal-footer">
          <button class="secondary-btn" @click="selectedReport = null">Close</button>
        </div>
      </div>
    </div>

    <!-- Generate report modal -->
    <div v-if="showGenerateModal" class="modal-overlay" @click="showGenerateModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Generate Monthly Report</h2>
          <button class="close-btn" @click="showGenerateModal = false">
            <XIcon />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="month-select">Select Month</label>
            <input type="month" id="month-select" v-model="selectedMonth" :max="currentMonth" class="month-input" />
          </div>
          <p class="info-text">
            <InfoIcon class="mini-icon" />
            This will generate a report for all your activities in the selected month.
          </p>
        </div>
        <div class="modal-footer">
          <button class="secondary-btn" @click="showGenerateModal = false">Cancel</button>
          <button class="primary-btn" @click="generateReport" :disabled="isGenerating">
            <LoaderIcon v-if="isGenerating" class="mini-icon spin" />
            <span v-else>Generate Report</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
  
<script>
import { ref, onMounted, computed } from 'vue'
import {
  FileIcon, FileTextIcon, PlusIcon, XIcon,
  LoaderIcon, AlertCircleIcon,
  ClockIcon, CalendarIcon, InfoIcon
} from 'lucide-vue-next'
import axios from 'axios'

export default {
  name: 'ReportView',
  components: {
    FileIcon, FileTextIcon, PlusIcon, XIcon,
    LoaderIcon, AlertCircleIcon,
    ClockIcon, CalendarIcon, InfoIcon
  },
  props: {
    nurseId: {
      type: String,
      required: false,
      default: null
    }
  },
  setup(props) {
    const nurseId = ref(localStorage.getItem('userId'))
    const reports = ref([])
    const loading = ref(true)
    const error = ref(null)
    const selectedReport = ref(null)
    const reportContent = ref('')
    const showGenerateModal = ref(false)
    const selectedMonth = ref(getCurrentMonth())
    const isGenerating = ref(false)

    const currentMonth = computed(() => {
      return getCurrentMonth()
    })

    function getCurrentMonth() {
      const now = new Date()
      return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    }

    function formatMonth(monthStr) {
      if (!monthStr) return 'Unknown'
      const [year, month] = monthStr.split('-')
      const date = new Date(parseInt(year), parseInt(month) - 1, 1)
      return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    }

    function formatDate(dateStr) {
      if (!dateStr) return 'Unknown'
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    async function fetchReports() {
      loading.value = true
      error.value = null

      try {
        const response = await axios.get(`http://localhost:8000/api/reports/${nurseId.value}`)
        reports.value = response.data.sort((a, b) => {
          return new Date(b.reportMonth) - new Date(a.reportMonth)
        })
      } catch (err) {
        console.error('Error fetching reports:', err)
        error.value = 'Failed to load reports. Please try again later.'
      } finally {
        loading.value = false
      }
    }

    async function viewReport(report) {
      try {
        const response = await axios.get(
          `http://localhost:8000/api/reports/${nurseId.value}/${report.reportMonth}`
        )
        reportContent.value = response.data.reportContent
        selectedReport.value = report
      } catch (err) {
        console.error('Error fetching report content:', err)
        error.value = 'Failed to load report content. Please try again later.'
      }
    }

    async function generateReport() {
      if (!selectedMonth.value) return;

      isGenerating.value = true;

      try {
        const query = `
      mutation GenerateReport(
        $nurseId: ID!
        $month: String!
        $includeHours: Boolean = true
        $includeEarnings: Boolean = true
      ) {
        generateReport(
          nurseId: $nurseId
          month: $month
          includeHours: $includeHours
          includeEarnings: $includeEarnings
        ) {
          success
          message
          month
          hours @include(if: $includeHours)
          earnings @include(if: $includeEarnings)
          cancellationRate
        }
      }
    `;

        const variables = {
          nurseId: nurseId.value,
          month: selectedMonth.value
        };

        const response = await axios.post(
          'http://localhost:8000/api/generate_report/graphql',
          { query, variables },
          { headers: { 'Content-Type': 'application/json' } }
        );

        // Handle GraphQL errors (different from HTTP errors)
        if (response.data.errors) {
          throw new Error(response.data.errors[0].message)
        }

        const result = response.data.data.generateReport

        if (!result.success) {
          throw new Error(result.message || 'Failed to generate report')
        }

        // Close modal and refresh reports
        showGenerateModal.value = false
        await fetchReports()

        // Show success message
        alert(`Report for ${formatMonth(selectedMonth.value)} has been generated successfully!`)

        // You can access other returned fields if needed:
        console.log('Report details:', {
          hours: result.hours,
          bookings: result.totalBookings,
          cancellationRate: result.cancellationRate
        })

      } catch (err) {
        console.error('Error generating report:', err)
        error.value = `Failed to generate report: ${err.message}`
      } finally {
        isGenerating.value = false
      }
    }


    onMounted(() => {
      if (!nurseId.value) {
        error.value = 'No nurse ID found. Please log in again.'
        loading.value = false
        return
      }
      fetchReports()
    })

    return {
      nurseId,
      reports,
      loading,
      error,
      selectedReport,
      reportContent,
      showGenerateModal,
      selectedMonth,
      isGenerating,
      currentMonth,
      formatMonth,
      formatDate,
      viewReport,
      generateReport
    }
  }
}
</script>
  
<style scoped>
.reports-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.generate-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.25rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.generate-btn:hover {
  background-color: #388e3c;
}

.loading,
.error-message,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin: 2rem 0;
}

.loading .spin,
.error-message .icon,
.empty-state .icon {
  width: 48px;
  height: 48px;
  margin-bottom: 1rem;
  color: #757575;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: #d32f2f;
  background-color: #ffebee;
}

.error-message .icon {
  color: #d32f2f;
}

.reports-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.report-card {
  display: flex;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.report-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.report-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background-color: #e3f2fd;
  border-radius: 8px;
  margin-right: 1rem;
  color: #1976d2;
}

.report-details {
  flex: 1;
}

.report-details h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
}

.report-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #616161;
}

.report-date {
  font-size: 0.8rem;
  color: #9e9e9e;
}

.report-actions {
  display: flex;
  align-items: flex-start;
}

.view-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background-color: #f5f5f5;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.view-btn:hover {
  background-color: #e0e0e0;
}

.mini-icon {
  width: 16px;
  height: 16px;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #757575;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  background-color: #f5f5f5;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.primary-btn,
.secondary-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.primary-btn {
  background-color: #1976d2;
  color: white;
  border: none;
}

.primary-btn:hover {
  background-color: #1565c0;
}

.primary-btn:disabled {
  background-color: #bbdefb;
  cursor: not-allowed;
}

.secondary-btn {
  background-color: white;
  color: #616161;
  border: 1px solid #e0e0e0;
}

.secondary-btn:hover {
  background-color: #f5f5f5;
}

/* Form styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.month-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
}

.info-text {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #e3f2fd;
  border-radius: 4px;
  color: #0d47a1;
  font-size: 0.9rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .reports-container {
    padding: 1rem;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .reports-list {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    max-height: 95vh;
  }
}
</style>