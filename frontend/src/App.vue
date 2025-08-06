<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top modern-nav-dark">
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
              <router-link class="nav-link nav-link-dark" to="/admin/dash">
                <i class="fas fa-tachometer-alt"></i> Dashboard
              </router-link>
            </li>
            <!-- User Navigation -->
            <li
              class="nav-item"
              v-else-if="userInSession && userSession.role === 'user'"
            >
              <router-link class="nav-link nav-link-dark" to="/user/dash">
                <i class="fas fa-home"></i> Dashboard
              </router-link>
            </li>
            <li
              class="nav-item"
              v-if="userInSession && userSession.role === 'user'"
            >
              <router-link class="nav-link nav-link-dark" to="/user/booking">
                <i class="fas fa-calendar-check"></i> My Bookings
              </router-link>
            </li>
          </ul>

          <!-- Search Bar -->
          <div class="search-container me-3" v-if="userInSession">
            <div class="input-group">
              <input
                class="form-control search-input-dark"
                v-model="searchTerm"
                @keyup.enter="search"
                placeholder="Search shows..."
                type="text"
              />
              <button class="btn btn-search-dark" @click="search" type="button">
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
              <button class="btn btn-danger-dark btn-sm" @click="logout">
                <i class="fas fa-sign-out-alt"></i> Logout
              </button>
            </li>
            <li class="nav-item" v-else>
              <router-link class="btn btn-primary-dark btn-sm" to="/login">
                <i class="fas fa-sign-in-alt"></i> Login
              </router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <main class="main-content-dark">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="modern-footer-dark mt-5">
      <div class="container">
        <div class="row">
          <div class="col-md-8">
            <p class="mb-0">
              &copy; 2024 TicketShow. Your premier destination for show
              bookings.
            </p>
          </div>
          <div class="col-md-4 text-end">
            <small class="text-muted">
              Made with ❤️ for entertainment lovers
            </small>
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

/* Dark Mode CSS Variables */
:root {
  --primary-color: #8b5cf6;
  --primary-dark: #7c3aed;
  --primary-light: #a78bfa;
  --secondary-color: #6366f1;
  --secondary-dark: #4f46e5;
  --accent-color: #06b6d4;
  --accent-dark: #0891b2;

  /* Dark Theme Colors */
  --bg-primary: #0f0f23;
  --bg-secondary: #1a1a2e;
  --bg-tertiary: #16213e;
  --bg-card: #1e293b;
  --bg-card-hover: #334155;

  /* Text Colors */
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --text-accent: #60a5fa;

  /* Status Colors */
  --success-color: #10b981;
  --success-dark: #059669;
  --danger-color: #ef4444;
  --danger-dark: #dc2626;
  --warning-color: #f59e0b;
  --warning-dark: #d97706;
  --info-color: #3b82f6;
  --info-dark: #2563eb;

  /* Border and Shadow */
  --border-color: #374151;
  --border-light: #4b5563;
  --border-focus: var(--primary-color);
  --shadow-dark: 0 10px 25px rgba(0, 0, 0, 0.5);
  --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.3);
  --shadow-hover: 0 8px 30px rgba(0, 0, 0, 0.4);

  /* Other Variables */
  --border-radius: 12px;
  --border-radius-lg: 16px;
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Dark Mode Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: linear-gradient(
    135deg,
    var(--bg-primary) 0%,
    var(--bg-secondary) 100%
  );
  color: var(--text-primary);
  min-height: 100vh;
}

#app {
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

/* Dark Navigation */
.modern-nav-dark {
  background: linear-gradient(
    135deg,
    var(--bg-secondary) 0%,
    var(--bg-tertiary) 100%
  );
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-dark);
  border-bottom: 1px solid var(--border-color);
  padding: 1rem 0;
}

.brand-logo {
  display: flex;
  align-items: center;
  text-decoration: none !important;
  font-weight: 700;
  font-size: 1.5rem;
  color: var(--text-primary) !important;
  transition: var(--transition);
}

.brand-logo:hover {
  transform: translateY(-2px);
  color: var(--primary-light) !important;
}

.brand-icon {
  font-size: 1.8rem;
  margin-right: 0.5rem;
  background: linear-gradient(45deg, var(--primary-color), var(--accent-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-text {
  background: linear-gradient(45deg, var(--text-primary), var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-link-dark {
  color: var(--text-secondary) !important;
  font-weight: 500;
  padding: 0.5rem 1rem !important;
  border-radius: var(--border-radius);
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-link-dark:hover,
.nav-link-dark.router-link-active {
  background: rgba(139, 92, 246, 0.15);
  color: var(--primary-light) !important;
  transform: translateY(-1px);
}

/* Dark Search Container */
.search-container {
  min-width: 280px;
}

.search-input-dark {
  border: 2px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-primary);
  border-radius: 25px 0 0 25px;
  padding: 0.5rem 1rem;
  transition: var(--transition);
}

.search-input-dark::placeholder {
  color: var(--text-muted);
}

.search-input-dark:focus {
  background: var(--bg-card-hover);
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  color: var(--text-primary);
}

.btn-search-dark {
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  border-left: none;
  color: var(--text-secondary);
  border-radius: 0 25px 25px 0;
  padding: 0.5rem 1rem;
  transition: var(--transition);
}

.btn-search-dark:hover {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

/* Dark Button Styles */
.btn {
  border-radius: var(--border-radius);
  font-weight: 500;
  padding: 0.5rem 1rem;
  transition: var(--transition);
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-dark)
  );
  color: white;
  text-decoration: none;
}

.btn-primary-dark:hover {
  background: linear-gradient(
    135deg,
    var(--primary-dark),
    var(--primary-color)
  );
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
  color: white;
}

.btn-danger-dark {
  background: linear-gradient(135deg, var(--danger-color), var(--danger-dark));
  color: white;
}

.btn-danger-dark:hover {
  background: linear-gradient(135deg, var(--danger-dark), var(--danger-color));
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
  color: white;
}

.btn-outline-light {
  border: 2px solid rgba(241, 245, 249, 0.3);
  color: var(--text-primary);
  background: transparent;
}

.btn-outline-light:hover {
  background: rgba(241, 245, 249, 0.1);
  border-color: var(--text-primary);
  color: var(--text-primary);
  transform: translateY(-2px);
}

/* Dark Main Content */
.main-content-dark {
  flex: 1;
  padding: 2rem 0;
  min-height: calc(100vh - 200px);
  background: var(--bg-primary);
}

/* Dark Footer */
.modern-footer-dark {
  background: linear-gradient(
    135deg,
    var(--bg-secondary) 0%,
    var(--bg-tertiary) 100%
  );
  color: var(--text-secondary);
  padding: 2rem 0;
  margin-top: auto;
  border-top: 1px solid var(--border-color);
}

.modern-footer-dark p {
  margin: 0;
}

/* Dark Card Improvements */
.card {
  border: none;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-card);
  transition: var(--transition);
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-hover);
  background: var(--bg-card-hover);
}

.card-header {
  background: linear-gradient(
    135deg,
    var(--bg-card) 0%,
    var(--bg-card-hover) 100%
  );
  border-bottom: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
  padding: 1.5rem;
  color: var(--text-primary);
}

.card-body {
  padding: 1.5rem;
  background: var(--bg-card);
  color: var(--text-primary);
}

/* Dark Form Controls */
.form-control {
  border-radius: var(--border-radius);
  border: 2px solid var(--border-color);
  padding: 0.75rem 1rem;
  transition: var(--transition);
  font-size: 0.95rem;
  background: var(--bg-card);
  color: var(--text-primary);
}

.form-control::placeholder {
  color: var(--text-muted);
}

.form-control:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.form-select {
  border-radius: var(--border-radius);
  border: 2px solid var(--border-color);
  padding: 0.75rem 1rem;
  transition: var(--transition);
  background: var(--bg-card);
  color: var(--text-primary);
}

.form-select:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.form-label {
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 0.5rem;
}

/* Dark Alert Styles */
.alert {
  border-radius: var(--border-radius);
  border: none;
  padding: 1rem 1.5rem;
  margin: 1rem 0;
}

.alert-danger {
  background: linear-gradient(
    135deg,
    rgba(239, 68, 68, 0.15),
    rgba(220, 38, 38, 0.1)
  );
  color: #fca5a5;
  border-left: 4px solid var(--danger-color);
}

.alert-success {
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.15),
    rgba(5, 150, 105, 0.1)
  );
  color: #6ee7b7;
  border-left: 4px solid var(--success-color);
}

.alert-info {
  background: linear-gradient(
    135deg,
    rgba(59, 130, 246, 0.15),
    rgba(37, 99, 235, 0.1)
  );
  color: #93c5fd;
  border-left: 4px solid var(--info-color);
}

.alert-warning {
  background: linear-gradient(
    135deg,
    rgba(245, 158, 11, 0.15),
    rgba(217, 119, 6, 0.1)
  );
  color: #fcd34d;
  border-left: 4px solid var(--warning-color);
}

/* Dark Utility Classes */
.text-gradient-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--accent-color)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.shadow-soft-dark {
  box-shadow: var(--shadow-card);
}

.rounded-lg {
  border-radius: var(--border-radius-lg);
}

.bg-dark-card {
  background: var(--bg-card);
  color: var(--text-primary);
}

.bg-dark-primary {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.text-primary-dark {
  color: var(--text-primary);
}

.text-secondary-dark {
  color: var(--text-secondary);
}

.text-muted-dark {
  color: var(--text-muted);
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

/* Dark Mode Scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--border-light);
}
</style>
