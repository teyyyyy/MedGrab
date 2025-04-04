<template>
  <div>
    <nav>
      <router-link to="/report">Reports</router-link>
      <br>
      <router-link to="/bookingcreator">Patient Booking Creator</router-link>
      <br>
      <router-link to="/bookingmanager">Nurse Booking Manager</router-link>
    </nav>
    <router-view />
  </div>
</template>
<script setup lang="ts">
</script>