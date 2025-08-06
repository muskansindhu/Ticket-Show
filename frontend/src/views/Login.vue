<template>
  <div class="login-container-dark">
    <div class="login-background-dark">
      <div class="background-shapes-dark">
        <div class="shape-dark shape-1"></div>
        <div class="shape-dark shape-2"></div>
        <div class="shape-dark shape-3"></div>
      </div>
    </div>

    <div class="container">
      <div class="row justify-content-center align-items-center min-vh-100">
        <div class="col-lg-5 col-md-7 col-sm-9">
          <div class="login-card-dark fade-in-up">
            <div class="login-header-dark">
              <div class="logo-section">
                <i class="fas fa-ticket-alt logo-icon-dark"></i>
                <h2 class="brand-name-dark">TicketShow</h2>
              </div>
              <p class="welcome-text-dark">
                {{ register ? "Create your account" : "Welcome back!" }}
              </p>
            </div>

            <div class="login-body-dark">
              <form
                @submit.prevent="register ? registerOn() : login()"
                class="login-form-dark"
              >
                <div class="form-floating-dark mb-3">
                  <input
                    type="text"
                    id="username"
                    class="form-control-dark modern-input-dark"
                    placeholder="Username"
                    v-model="username"
                    required
                  />
                  <label for="username" class="form-label-dark">
                    <i class="fas fa-user me-2"></i>Username
                  </label>
                </div>

                <div class="form-floating-dark mb-3" v-if="register">
                  <input
                    type="email"
                    id="email"
                    class="form-control-dark modern-input-dark"
                    placeholder="Email"
                    v-model="email"
                    required
                  />
                  <label for="email" class="form-label-dark">
                    <i class="fas fa-envelope me-2"></i>Email Address
                  </label>
                </div>

                <div class="form-floating-dark mb-3">
                  <input
                    type="password"
                    id="password"
                    class="form-control-dark modern-input-dark"
                    placeholder="Password"
                    minlength="4"
                    v-model="password"
                    required
                  />
                  <label for="password" class="form-label-dark">
                    <i class="fas fa-lock me-2"></i>Password
                  </label>
                </div>

                <div class="mb-4">
                  <label class="form-label role-label-dark">
                    <i class="fas fa-user-tag me-2"></i>Account Type
                  </label>
                  <div class="role-selector-dark">
                    <input
                      type="radio"
                      id="user-role"
                      value="user"
                      v-model="role"
                      class="role-input-dark"
                    />
                    <label for="user-role" class="role-option-dark">
                      <i class="fas fa-user"></i>
                      <span>User</span>
                    </label>

                    <input
                      type="radio"
                      id="admin-role"
                      value="admin"
                      v-model="role"
                      class="role-input-dark"
                    />
                    <label for="admin-role" class="role-option-dark">
                      <i class="fas fa-user-shield"></i>
                      <span>Admin</span>
                    </label>
                  </div>
                </div>

                <button
                  class="btn btn-primary-dark btn-lg w-100 modern-btn-dark"
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

              <div class="login-divider-dark">
                <span>or</span>
              </div>

              <div class="switch-mode-dark">
                <p class="switch-text-dark">
                  {{
                    register
                      ? "Already have an account?"
                      : "Don't have an account?"
                  }}
                  <a @click="state" href="#" class="switch-link-dark">
                    {{ register ? "Sign In" : "Sign Up" }}
                  </a>
                </p>
              </div>

              <div class="alert alert-danger modern-alert-dark" v-if="error">
                <i class="fas fa-exclamation-triangle me-2"></i>
                {{ msg }}
              </div>
            </div>
          </div>

          <div class="features-section-dark">
            <div class="feature-item-dark">
              <i class="fas fa-shield-alt"></i>
              <span>Secure & Trusted</span>
            </div>
            <div class="feature-item-dark">
              <i class="fas fa-clock"></i>
              <span>24/7 Support</span>
            </div>
            <div class="feature-item-dark">
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
.login-container-dark {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 2rem 0;
  background: var(--bg-primary);
}

.login-background-dark {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  z-index: -1;
}

.background-shapes-dark {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.shape-dark {
  position: absolute;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.1);
  animation: float 6s ease-in-out infinite;
  backdrop-filter: blur(2px);
}

.shape-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: -10%;
  animation-delay: 0s;
  background: rgba(139, 92, 246, 0.08);
}

.shape-2 {
  width: 200px;
  height: 200px;
  top: 60%;
  right: -5%;
  animation-delay: 2s;
  background: rgba(99, 102, 241, 0.08);
}

.shape-3 {
  width: 150px;
  height: 150px;
  bottom: 10%;
  left: 20%;
  animation-delay: 4s;
  background: rgba(6, 182, 212, 0.08);
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.8;
  }
  50% {
    transform: translateY(-20px) rotate(10deg);
    opacity: 1;
  }
}

.login-card-dark {
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
  overflow: hidden;
  transition: all 0.3s ease;
}

.login-card-dark:hover {
  transform: translateY(-5px);
  box-shadow: 0 35px 60px rgba(0, 0, 0, 0.6);
  border-color: rgba(139, 92, 246, 0.3);
}

.login-header-dark {
  padding: 2.5rem 2.5rem 1rem;
  text-align: center;
  background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.1) 0%,
    rgba(99, 102, 241, 0.1) 100%
  );
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.logo-section {
  margin-bottom: 1rem;
}

.logo-icon-dark {
  font-size: 3rem;
  background: linear-gradient(135deg, #8b5cf6, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.3));
}

.brand-name-dark {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #f1f5f9, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-text-dark {
  color: var(--text-secondary);
  font-size: 1.1rem;
  margin: 0;
}

.login-body-dark {
  padding: 1rem 2.5rem 2.5rem;
  background: rgba(30, 41, 59, 0.8);
}

.login-form-dark {
  margin-bottom: 1.5rem;
}

.form-floating-dark {
  position: relative;
  margin-bottom: 1rem;
}

.modern-input-dark {
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem 1rem 1rem 3rem;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: var(--bg-card);
  color: var(--text-primary);
  width: 100%;
}

.modern-input-dark::placeholder {
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.modern-input-dark:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.15);
  background: var(--bg-card-hover);
  outline: none;
}

.modern-input-dark:focus::placeholder {
  opacity: 1;
}

.form-label-dark {
  position: absolute;
  top: 50%;
  left: 3rem;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s ease;
  background: var(--bg-card);
  padding: 0 0.5rem;
}

.modern-input-dark:focus + .form-label-dark,
.modern-input-dark:not(:placeholder-shown) + .form-label-dark {
  top: 0;
  left: 2.5rem;
  font-size: 0.8rem;
  color: var(--primary-color);
  background: var(--bg-card);
}

.form-label-dark i {
  position: absolute;
  left: -2rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  z-index: 10;
}

.role-label-dark {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
}

.role-selector-dark {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.role-input-dark {
  display: none;
}

.role-option-dark {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--bg-card);
  color: var(--text-secondary);
}

.role-option-dark:hover {
  border-color: var(--primary-color);
  background: rgba(139, 92, 246, 0.05);
  color: var(--text-primary);
}

.role-input-dark:checked + .role-option-dark {
  border-color: var(--primary-color);
  background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.15) 0%,
    rgba(99, 102, 241, 0.1) 100%
  );
  color: var(--primary-light);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
}

.role-option-dark i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.role-option-dark span {
  font-weight: 500;
}

.modern-btn-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-dark)
  );
  border: none;
  border-radius: 12px;
  padding: 1rem;
  font-weight: 600;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  color: white;
}

.modern-btn-dark:hover {
  background: linear-gradient(135deg, var(--primary-dark), var(--accent-color));
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.4);
  color: white;
}

.modern-btn-dark:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.login-divider-dark {
  text-align: center;
  margin: 1.5rem 0;
  position: relative;
}

.login-divider-dark::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-color);
}

.login-divider-dark span {
  background: rgba(30, 41, 59, 0.95);
  padding: 0 1rem;
  color: var(--text-muted);
  font-weight: 500;
}

.switch-mode-dark {
  text-align: center;
}

.switch-text-dark {
  color: var(--text-secondary);
  margin: 0;
}

.switch-link-dark {
  color: var(--primary-light);
  text-decoration: none;
  font-weight: 600;
  margin-left: 0.5rem;
  transition: color 0.3s ease;
}

.switch-link-dark:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

.modern-alert-dark {
  border: none;
  border-radius: 12px;
  background: linear-gradient(
    135deg,
    rgba(239, 68, 68, 0.15),
    rgba(220, 38, 38, 0.1)
  );
  color: #fca5a5;
  padding: 1rem;
  margin-top: 1rem;
  border-left: 4px solid var(--danger-color);
}

.features-section-dark {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 2rem;
  padding: 1rem;
}

.feature-item-dark {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-align: center;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.feature-item-dark:hover {
  opacity: 1;
  color: var(--primary-light);
  transform: translateY(-2px);
}

.feature-item-dark i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--accent-color)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  .login-header-dark,
  .login-body-dark {
    padding: 1.5rem;
  }

  .brand-name-dark {
    font-size: 1.5rem;
  }

  .logo-icon-dark {
    font-size: 2rem;
  }

  .role-selector-dark {
    flex-direction: column;
  }

  .features-section-dark {
    gap: 1rem;
  }

  .feature-item-dark {
    font-size: 0.8rem;
  }

  .shape-dark {
    display: none;
  }
}

@media (max-width: 480px) {
  .login-container-dark {
    padding: 1rem 0;
  }

  .login-card-dark {
    margin: 0 1rem;
    border-radius: 16px;
  }

  .modern-input-dark {
    padding: 0.875rem 0.875rem 0.875rem 2.5rem;
  }

  .form-label-dark {
    left: 2.5rem;
  }

  .form-label-dark i {
    left: -1.75rem;
  }
}

/* Focus states for better accessibility */
.modern-input-dark:focus,
.role-option-dark:focus-within {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Loading state for button */
.modern-btn-dark.loading {
  position: relative;
}

.modern-btn-dark.loading::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}
</style>
