<template>
  <div class="login-container">
    <div class="login-background">
      <div class="background-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>

    <div class="container">
      <div class="row justify-content-center align-items-center min-vh-100">
        <div class="col-lg-5 col-md-7 col-sm-9">
          <div class="login-card fade-in-up">
            <div class="login-header">
              <div class="logo-section">
                <i class="fas fa-ticket-alt logo-icon"></i>
                <h2 class="brand-name">TicketShow</h2>
              </div>
              <p class="welcome-text">
                {{ register ? "Create your account" : "Welcome back!" }}
              </p>
            </div>

            <div class="login-body">
              <form
                @submit.prevent="register ? registerOn() : login()"
                class="login-form"
              >
                <div class="form-floating mb-3">
                  <input
                    type="text"
                    id="username"
                    class="form-control modern-input"
                    placeholder="Username"
                    v-model="username"
                    required
                  />
                  <label for="username">
                    <i class="fas fa-user me-2"></i>Username
                  </label>
                </div>

                <div class="form-floating mb-3" v-if="register">
                  <input
                    type="email"
                    id="email"
                    class="form-control modern-input"
                    placeholder="Email"
                    v-model="email"
                    required
                  />
                  <label for="email">
                    <i class="fas fa-envelope me-2"></i>Email Address
                  </label>
                </div>

                <div class="form-floating mb-3">
                  <input
                    type="password"
                    id="password"
                    class="form-control modern-input"
                    placeholder="Password"
                    minlength="4"
                    v-model="password"
                    required
                  />
                  <label for="password">
                    <i class="fas fa-lock me-2"></i>Password
                  </label>
                </div>

                <div class="mb-4">
                  <label class="form-label role-label">
                    <i class="fas fa-user-tag me-2"></i>Account Type
                  </label>
                  <div class="role-selector">
                    <input
                      type="radio"
                      id="user-role"
                      value="user"
                      v-model="role"
                      class="role-input"
                    />
                    <label for="user-role" class="role-option">
                      <i class="fas fa-user"></i>
                      <span>User</span>
                    </label>

                    <input
                      type="radio"
                      id="admin-role"
                      value="admin"
                      v-model="role"
                      class="role-input"
                    />
                    <label for="admin-role" class="role-option">
                      <i class="fas fa-user-shield"></i>
                      <span>Admin</span>
                    </label>
                  </div>
                </div>

                <button
                  class="btn btn-primary btn-lg w-100 modern-btn"
                  type="submit"
                  :disabled="register && !isEmail(email)"
                >
                  <i
                    class="fas"
                    :class="register ? 'fa-user-plus' : 'fa-sign-in-alt'"
                  ></i>
                  {{ register ? "Create Account" : "Sign In" }}
                </button>
              </form>

              <div class="login-divider">
                <span>or</span>
              </div>

              <div class="switch-mode">
                <p class="switch-text">
                  {{
                    register
                      ? "Already have an account?"
                      : "Don't have an account?"
                  }}
                  <a @click="state" href="#" class="switch-link">
                    {{ register ? "Sign In" : "Sign Up" }}
                  </a>
                </p>
              </div>

              <div class="alert alert-danger modern-alert" v-if="error">
                <i class="fas fa-exclamation-triangle me-2"></i>
                {{ msg }}
              </div>
            </div>
          </div>

          <div class="features-section">
            <div class="feature-item">
              <i class="fas fa-shield-alt"></i>
              <span>Secure & Trusted</span>
            </div>
            <div class="feature-item">
              <i class="fas fa-clock"></i>
              <span>24/7 Support</span>
            </div>
            <div class="feature-item">
              <i class="fas fa-star"></i>
              <span>Best Shows</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "LoginView",
  data() {
    return {
      userSession: JSON.parse(localStorage.getItem("userSession")) || null,
      register: false,
      username: "",
      email: "",
      password: "",
      role: "user",
      token: "",
      exp: "",
      msg: "",
      error: false,
    };
  },
  methods: {
    isEmail(str) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(str);
    },
    click() {
      if (this.role === "admin") {
        this.$router.push("/admin/dash");
        this.$router.go();
      } else {
        this.$router.push("/user/dash");
        this.$router.go();
      }
    },
    state() {
      this.error = false;
      this.register = !this.register;
    },
    async registerOn() {
      if (
        this.isEmail(this.email) &&
        this.username.trim() &&
        this.password.length > 3
      ) {
        try {
          const formData = new FormData();
          formData.append("username", this.username);
          formData.append("email", this.email);
          formData.append("password", this.password);

          const response = await axios.post(
            `http://127.0.0.1:1234/vue/${this.role}`,
            formData
          );

          if ("error" in response.data) {
            throw new Error(response.data.error_msg);
          }

          this.token = response.data.token;
          this.exp = response.data.exp;

          this.userSession = {
            token: this.token,
            exp: this.exp,
            role: this.role,
          };

          localStorage.setItem("userSession", JSON.stringify(this.userSession));
          this.click();
        } catch (error) {
          this.error = true;
          this.msg = error.message;
        }
      } else {
        this.msg = "Fields not filled properly";
        this.error = true;
      }
    },
    async login() {
      try {
        let loginEndpoint = "";

        if (this.role === "user") {
          loginEndpoint = "http://127.0.0.1:1234/vue/user/login";
        } else if (this.role === "admin") {
          loginEndpoint = "http://127.0.0.1:1234/vue/admin/login";
        }

        if (!loginEndpoint) {
          throw new Error("Invalid role selected");
        }

        const response = await axios.post(loginEndpoint, {
          username: this.username,
          password: this.password,
        });

        if ("error" in response.data) {
          throw new Error(response.data.error_msg);
        }
        this.token = response.data.token;
        this.exp = response.data.exp;

        this.userSession = {
          token: this.token,
          exp: this.exp,
          role: this.role,
        };

        localStorage.setItem("userSession", JSON.stringify(this.userSession));

        if (this.role === "admin") {
          this.redirectToAdminDash();
        } else {
          this.redirectToUserDash();
        }
        //window.location.reload();
        this.$router.go();
      } catch (error) {
        this.error = true;
        this.errorMsg = error.message;
      }
    },
    redirectToAdminDash() {
      this.$router.push("/admin/dash");
    },

    redirectToUserDash() {
      this.$router.push("/user/dash");
    },
  },
  mounted() {
    document.title = this.register ? "Register" : "Login";
  },
};
</script>

<style scoped>
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 2rem 0;
}

.login-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: -1;
}

.background-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: -10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  top: 60%;
  right: -5%;
  animation-delay: 2s;
}

.shape-3 {
  width: 150px;
  height: 150px;
  bottom: 10%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(10deg);
  }
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
  transition: all 0.3s ease;
}

.login-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 35px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  padding: 2.5rem 2.5rem 1rem;
  text-align: center;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.1),
    rgba(118, 75, 162, 0.1)
  );
}

.logo-section {
  margin-bottom: 1rem;
}

.logo-icon {
  font-size: 3rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.brand-name {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-text {
  color: #6b7280;
  font-size: 1.1rem;
  margin: 0;
}

.login-body {
  padding: 1rem 2.5rem 2.5rem;
}

.login-form {
  margin-bottom: 1.5rem;
}

.form-floating {
  position: relative;
}

.modern-input {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem 1rem 1rem 3rem;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
}

.modern-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  background: white;
}

.form-floating label {
  padding-left: 3rem;
  color: #6b7280;
  font-weight: 500;
}

.form-floating label i {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  z-index: 10;
}

.role-label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.role-selector {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.role-input {
  display: none;
}

.role-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
}

.role-option:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.role-input:checked + .role-option {
  border-color: #667eea;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.1),
    rgba(118, 75, 162, 0.1)
  );
  color: #667eea;
}

.role-option i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.role-option span {
  font-weight: 500;
}

.modern-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 12px;
  padding: 1rem;
  font-weight: 600;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.modern-btn:hover {
  background: linear-gradient(135deg, #5a6fd8, #6b46a3);
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.modern-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.login-divider {
  text-align: center;
  margin: 1.5rem 0;
  position: relative;
}

.login-divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e5e7eb;
}

.login-divider span {
  background: rgba(255, 255, 255, 0.95);
  padding: 0 1rem;
  color: #6b7280;
  font-weight: 500;
}

.switch-mode {
  text-align: center;
}

.switch-text {
  color: #6b7280;
  margin: 0;
}

.switch-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-left: 0.5rem;
  transition: color 0.3s ease;
}

.switch-link:hover {
  color: #5a6fd8;
  text-decoration: underline;
}

.modern-alert {
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  color: #dc2626;
  padding: 1rem;
  margin-top: 1rem;
  border-left: 4px solid #dc2626;
}

.features-section {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 2rem;
  padding: 1rem;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  text-align: center;
}

.feature-item i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  opacity: 0.8;
}

.fade-in-up {
  animation: fadeInUp 0.8s ease-out;
}

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

/* Responsive Design */
@media (max-width: 768px) {
  .login-header,
  .login-body {
    padding: 1.5rem;
  }

  .brand-name {
    font-size: 1.5rem;
  }

  .logo-icon {
    font-size: 2rem;
  }

  .role-selector {
    flex-direction: column;
  }

  .features-section {
    gap: 1rem;
  }

  .feature-item {
    font-size: 0.8rem;
  }

  .shape {
    display: none;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 1rem 0;
  }

  .login-card {
    margin: 0 1rem;
    border-radius: 16px;
  }
}
</style>
