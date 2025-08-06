<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top modern-nav">
      <div class="container">
        <router-link class="navbar-brand brand-logo" to="/">
          <i class="fas fa-ticket-alt brand-icon"></i>
          <span class="brand-text">TicketShow</span>
        </router-link>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <!-- Admin Navigation -->
            <li
              class="nav-item"
              v-if="userInSession && userSession.role === 'admin'"
            >
              <router-link class="nav-link nav-link-modern" to="/admin/dash">
                <i class="fas fa-tachometer-alt"></i> Dashboard
              </router-link>
            </li>
            <!-- User Navigation -->
            <li
              class="nav-item"
              v-else-if="userInSession && userSession.role === 'user'"
            >
              <router-link class="nav-link nav-link-modern" to="/user/dash">
                <i class="fas fa-home"></i> Dashboard
              </router-link>
            </li>
            <li
              class="nav-item"
              v-if="userInSession && userSession.role === 'user'"
            >
              <router-link class="nav-link nav-link-modern" to="/user/booking">
                <i class="fas fa-calendar-check"></i> My Bookings
              </router-link>
            </li>
          </ul>

          <!-- Search Bar -->
          <div class="search-container me-3" v-if="userInSession">
            <div class="input-group">
              <input
                class="form-control search-input"
                v-model="searchTerm"
                @keyup.enter="search"
                placeholder="Search shows..."
                type="text"
              />
              <button class="btn btn-search" @click="search" type="button">
                <i class="fas fa-search"></i>
              </button>
            </div>
          </div>

          <!-- Action Buttons -->
          <ul class="navbar-nav">
            <li class="nav-item" v-if="showGoBackButton">
              <button class="btn btn-outline-light btn-sm me-2" @click="goBack">
                <i class="fas fa-arrow-left"></i> Back
              </button>
            </li>
            <li class="nav-item" v-if="userInSession">
              <button class="btn btn-danger btn-sm" @click="logout">
                <i class="fas fa-sign-out-alt"></i> Logout
              </button>
            </li>
            <li class="nav-item" v-else>
              <router-link class="btn btn-primary btn-sm" to="/login">
                <i class="fas fa-sign-in-alt"></i> Login
              </router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="modern-footer mt-5">
      <div class="container">
        <div class="row">
          <div class="col-md-8">
            <p class="mb-0">
              &copy; 2024 TicketShow. Your premier destination for show
              bookings.
            </p>
          </div>
          <div class="col-md-4 text-end">
            <small class="text-muted"
              >Made with ❤️ for entertainment lovers</small
            >
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      userSession: JSON.parse(localStorage.getItem("userSession")) || null,
      user: null,
      searchTerm: "",
      searchResults: [],
    };
  },
  methods: {
    logout() {
      localStorage.removeItem("userSession");
      this.userSession = null;
      this.$router.push({ name: "login" });
    },
    async search() {
      this.$router.push(`/search/${this.searchTerm}`);
    },
    goBack() {
      // Go back to the previous page in history
      this.$router.go(-1);
    },
  },
  computed: {
    userInSession() {
      return this.userSession !== null;
    },
    showGoBackButton() {
      const currentPath = this.$route.path;
      return (
        currentPath !== "/admin/dash" &&
        currentPath !== "/user/dash" &&
        ((this.userInSession && this.userSession.role === "admin") ||
          (this.userInSession && this.userSession.role === "user"))
      );
    },
  },
};
</script>

<style>
/* Import Google Fonts */
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap");

/* CSS Variables for consistent theming */
:root {
  --primary-color: #667eea;
  --primary-dark: #5a6fd8;
  --secondary-color: #764ba2;
  --success-color: #48bb78;
  --danger-color: #f56565;
  --warning-color: #ed8936;
  --info-color: #4299e1;
  --light-color: #f7fafc;
  --dark-color: #2d3748;
  --gray-100: #f7fafc;
  --gray-200: #edf2f7;
  --gray-300: #e2e8f0;
  --gray-400: #cbd5e0;
  --gray-500: #a0aec0;
  --gray-600: #718096;
  --gray-700: #4a5568;
  --gray-800: #2d3748;
  --gray-900: #1a202c;
  --border-radius: 12px;
  --box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

#app {
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--dark-color);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Modern Navigation */
.modern-nav {
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem 0;
}

.brand-logo {
  display: flex;
  align-items: center;
  text-decoration: none !important;
  font-weight: 700;
  font-size: 1.5rem;
  color: white !important;
  transition: var(--transition);
}

.brand-logo:hover {
  transform: translateY(-2px);
  color: rgba(255, 255, 255, 0.9) !important;
}

.brand-icon {
  font-size: 1.8rem;
  margin-right: 0.5rem;
  background: linear-gradient(45deg, #fff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-text {
  background: linear-gradient(45deg, #fff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-link-modern {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
  padding: 0.5rem 1rem !important;
  border-radius: 8px;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-link-modern:hover,
.nav-link-modern.router-link-active {
  background: rgba(255, 255, 255, 0.15);
  color: white !important;
  transform: translateY(-1px);
}

/* Search Container */
.search-container {
  min-width: 280px;
}

.search-input {
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border-radius: 25px 0 0 25px;
  padding: 0.5rem 1rem;
  transition: var(--transition);
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.25);
  border: none;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
  color: white;
}

.btn-search {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  border-radius: 0 25px 25px 0;
  padding: 0.5rem 1rem;
  transition: var(--transition);
}

.btn-search:hover {
  background: rgba(255, 255, 255, 0.3);
  color: white;
}

/* Button Styles */
.btn {
  border-radius: 8px;
  font-weight: 500;
  padding: 0.5rem 1rem;
  transition: var(--transition);
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-dark)
  );
  color: white;
}

.btn-primary:hover {
  background: linear-gradient(
    135deg,
    var(--primary-dark),
    var(--primary-color)
  );
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
}

.btn-danger {
  background: linear-gradient(135deg, var(--danger-color), #e53e3e);
  color: white;
}

.btn-danger:hover {
  background: linear-gradient(135deg, #e53e3e, var(--danger-color));
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(245, 101, 101, 0.3);
}

.btn-outline-light {
  border: 2px solid rgba(255, 255, 255, 0.5);
  color: white;
  background: transparent;
}

.btn-outline-light:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: white;
  color: white;
  transform: translateY(-2px);
}

/* Main Content */
.main-content {
  flex: 1;
  padding: 2rem 0;
  min-height: calc(100vh - 200px);
}

/* Footer */
.modern-footer {
  background: var(--gray-800);
  color: var(--gray-300);
  padding: 2rem 0;
  margin-top: auto;
}

.modern-footer p {
  margin: 0;
}

/* Responsive Design */
@media (max-width: 768px) {
  .search-container {
    min-width: 100%;
    margin: 1rem 0;
  }

  .brand-text {
    font-size: 1.2rem;
  }

  .navbar-nav {
    margin-top: 1rem;
  }

  .navbar-nav .nav-item {
    margin: 0.25rem 0;
  }
}

/* Animation Classes */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.6s ease-out;
}

/* Card Improvements */
.card {
  border: none;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  transition: var(--transition);
  background: white;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.card-header {
  background: linear-gradient(135deg, var(--gray-100), white);
  border-bottom: 1px solid var(--gray-200);
  border-radius: var(--border-radius) var(--border-radius) 0 0;
  padding: 1.5rem;
}

.card-body {
  padding: 1.5rem;
}

/* Form Controls */
.form-control {
  border-radius: 8px;
  border: 2px solid var(--gray-300);
  padding: 0.75rem 1rem;
  transition: var(--transition);
  font-size: 0.95rem;
}

.form-control:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-select {
  border-radius: 8px;
  border: 2px solid var(--gray-300);
  padding: 0.75rem 1rem;
  transition: var(--transition);
}

.form-select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Alert Styles */
.alert {
  border-radius: var(--border-radius);
  border: none;
  padding: 1rem 1.5rem;
  margin: 1rem 0;
}

.alert-danger {
  background: linear-gradient(135deg, #fed7d7, #feb2b2);
  color: var(--danger-color);
}

.alert-success {
  background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
  color: var(--success-color);
}

/* Utility Classes */
.text-gradient {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--secondary-color)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.shadow-soft {
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
}

.rounded-lg {
  border-radius: var(--border-radius);
}
</style>
