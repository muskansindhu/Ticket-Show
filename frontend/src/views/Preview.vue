<template>
  <div class="preview-page-dark">
    <!-- Dark Hero Section -->
    <section class="hero-section-dark">
      <div class="hero-background-dark">
        <div class="hero-overlay-dark"></div>
        <div class="hero-shapes-dark">
          <div class="hero-shape-dark hero-shape-1"></div>
          <div class="hero-shape-dark hero-shape-2"></div>
          <div class="hero-shape-dark hero-shape-3"></div>
        </div>
      </div>

      <div class="container">
        <div class="row align-items-center min-vh-75">
          <div class="col-lg-6">
            <div class="hero-content-dark">
              <h1 class="hero-title-dark">
                <span class="title-highlight-dark">Premium</span>
                Entertainment
                <br />
                <span class="title-accent-dark">Awaits You</span>
              </h1>
              <p class="hero-description-dark">
                Discover and book the most exciting shows, theaters, and
                entertainment experiences. Your gateway to unforgettable moments
                starts here.
              </p>
              <div class="hero-stats-dark">
                <div class="stat-item-dark">
                  <div class="stat-number-dark">{{ theaters.length }}+</div>
                  <div class="stat-label-dark">Theaters</div>
                </div>
                <div class="stat-divider-dark"></div>
                <div class="stat-item-dark">
                  <div class="stat-number-dark">{{ totalShows }}+</div>
                  <div class="stat-label-dark">Shows</div>
                </div>
                <div class="stat-divider-dark"></div>
                <div class="stat-item-dark">
                  <div class="stat-number-dark">1000+</div>
                  <div class="stat-label-dark">Happy Customers</div>
                </div>
              </div>
              <div class="hero-actions-dark">
                <router-link
                  to="/login"
                  class="btn btn-primary-dark btn-lg hero-btn-dark"
                >
                  <i class="fas fa-ticket-alt me-2"></i>
                  Get Started
                </router-link>
                <button
                  class="btn btn-outline-light btn-lg hero-btn-secondary-dark"
                  @click="scrollToShows"
                >
                  <i class="fas fa-play-circle me-2"></i>
                  Explore Shows
                </button>
              </div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="hero-visual-dark">
              <div class="floating-cards-dark">
                <div class="floating-card-dark card-1">
                  <i class="fas fa-theater-masks"></i>
                  <span>Drama</span>
                </div>
                <div class="floating-card-dark card-2">
                  <i class="fas fa-music"></i>
                  <span>Musical</span>
                </div>
                <div class="floating-card-dark card-3">
                  <i class="fas fa-laugh"></i>
                  <span>Comedy</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Dark Shows Section -->
    <section class="shows-section-dark" id="shows">
      <div class="container">
        <div class="section-header-dark text-center">
          <h2 class="section-title-dark">
            <span class="title-accent-dark">Featured</span> Shows & Theaters
          </h2>
          <p class="section-description-dark">
            Discover amazing entertainment options across our premium theater
            network
          </p>
        </div>

        <div class="theaters-grid-dark" v-if="theaters.length > 0">
          <div
            class="theater-card-dark fade-in-up"
            v-for="(theater, index) in theaters"
            :key="index"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="theater-header-dark">
              <div class="theater-info-dark">
                <h3 class="theater-name-dark">
                  <i class="fas fa-building me-2"></i>
                  {{ theater.theater_name }}
                </h3>
                <p class="theater-location-dark">
                  <i class="fas fa-map-marker-alt me-2"></i>
                  {{ theater.location }}
                </p>
                <div class="theater-capacity-dark">
                  <i class="fas fa-users me-2"></i>
                  <span>Capacity: {{ theater.capacity }} seats</span>
                </div>
              </div>
              <div class="theater-badge-dark">
                <span class="badge bg-primary-dark">Premium</span>
              </div>
            </div>

            <div
              class="shows-grid-dark"
              v-if="theater.shows && theater.shows.length > 0"
            >
              <div
                class="show-card-dark"
                v-for="(show, showIndex) in theater.shows"
                :key="showIndex"
              >
                <div class="show-poster-dark">
                  <img
                    :src="posterImg(show.show_name)"
                    :alt="show.show_name"
                    class="poster-image-dark"
                    @error="handleImageError"
                  />
                  <div class="poster-overlay-dark">
                    <div class="show-actions-dark">
                      <button class="btn btn-sm btn-light-dark" disabled>
                        <i class="fas fa-eye me-1"></i>
                        Preview
                      </button>
                    </div>
                  </div>
                </div>

                <div class="show-info-dark">
                  <h4 class="show-title-dark">{{ show.show_name }}</h4>
                  <div class="show-details-dark">
                    <div class="show-time-dark">
                      <i class="fas fa-clock me-2"></i>
                      {{ formatTime(show.time) }}
                    </div>
                    <div class="show-seats-dark">
                      <i class="fas fa-chair me-2"></i>
                      {{ availableSeats(theater.capacity, show.seats_booked) }}
                      available
                    </div>
                  </div>

                  <div class="show-status-dark">
                    <template
                      v-if="
                        availableSeats(theater.capacity, show.seats_booked) > 0
                      "
                    >
                      <div class="availability-indicator-dark available">
                        <span class="indicator"></span>
                        Available
                      </div>
                    </template>
                    <template v-else>
                      <div class="availability-indicator-dark sold-out">
                        <span class="indicator"></span>
                        Sold Out
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <div class="no-shows-dark" v-else>
              <i class="fas fa-calendar-times"></i>
              <p>No shows currently scheduled</p>
            </div>
          </div>
        </div>

        <div class="loading-state-dark" v-else>
          <div class="loading-spinner-dark">
            <i class="fas fa-spinner fa-spin"></i>
          </div>
          <p>Loading amazing shows...</p>
        </div>
      </div>
    </section>

    <!-- Dark CTA Section -->
    <section class="cta-section-dark">
      <div class="container">
        <div class="cta-content-dark text-center">
          <h2 class="cta-title-dark">Ready to Experience Something Amazing?</h2>
          <p class="cta-description-dark">
            Join thousands of entertainment lovers and never miss a great show
            again.
          </p>
          <router-link
            to="/login"
            class="btn btn-primary-dark btn-lg cta-btn-dark"
          >
            <i class="fas fa-rocket me-2"></i>
            Start Your Journey
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "PreviewPage",
  data() {
    return {
      theaters: [],
      formData: {
        theater_name: "",
        location: "",
        capacity: "",
      },
    };
  },
  computed: {
    totalShows() {
      return this.theaters.reduce((total, theater) => {
        return total + (theater.shows ? theater.shows.length : 0);
      }, 0);
    },
  },
  methods: {
    async getTheater() {
      const path = "http://127.0.0.1:1234/vue/all/theater";
      try {
        const response = await axios.get(path);
        this.theaters = response.data.theaters;
        this.loadShowsForTheaters();
      } catch (error) {
        console.error("Error fetching theaters:", error);
      }
    },

    async getShowsForTheater(theater) {
      const path = `http://127.0.0.1:1234/vue/theater/${theater.roll}/show`;
      try {
        const response = await axios.get(path);
        this.$set(theater, "shows", response.data.show);
      } catch (error) {
        console.error(
          `Error fetching shows for theater ${theater.roll}:`,
          error
        );
      }
    },

    async addTheaterForm() {
      try {
        const formData = new FormData();
        formData.append("theater_name", this.formData.theater_name);
        formData.append("location", this.formData.location);
        formData.append("capacity", this.formData.capacity);

        const response = await axios.post(
          "http://127.0.0.1:1234/vue/theater",
          formData
        );

        console.log(response);
        this.getTheater();
      } catch (error) {
        console.error("AxiosError:", error);

        if (error.response) {
          console.error("Response Data:", error.response.data);
        } else {
          console.error("Network Error:", error.message);
        }
        alert("Oops! An error occurred. Theater was not added.");
      }
    },

    loadShowsForTheaters() {
      for (const theater of this.theaters) {
        this.getShowsForTheater(theater);
      }
    },

    initForm() {
      this.formData.theater_name = "";
      this.formData.location = "";
      this.formData.capacity = "";
    },

    onSubmit(e) {
      e.preventDefault();
      this.$refs.theaterModal.hide();
      const payload = {
        theater_name: this.formData.theater_name,
        location: this.formData.location,
        capacity: this.formData.capacity,
      };
      this.addTheaterForm(payload);
    },
    posterImg(showName) {
      return `http://127.0.0.1:1234/static/img/Posters/${showName}.webp`;
    },
    formatTime(time) {
      const [hours, minutes] = time.split(":");
      return `${hours}:${minutes}`;
    },
    availableSeats(totalCapacity, seatsBooked) {
      return totalCapacity - seatsBooked;
    },
    handleImageError(event) {
      event.target.src = "https://via.placeholder.com/200x300"; // Fallback image
    },
    scrollToShows() {
      const showsSection = document.getElementById("shows");
      if (showsSection) {
        showsSection.scrollIntoView({ behavior: "smooth" });
      }
    },
  },
  async created() {
    await this.getTheater();
  },
};
</script>

<style scoped>
.preview-page-dark {
  overflow-x: hidden;
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* Dark Hero Section */
.hero-section-dark {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  color: var(--text-primary);
}

.hero-background-dark {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  z-index: -1;
}

.hero-overlay-dark {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(15, 15, 35, 0.4);
}

.hero-shapes-dark {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.hero-shape-dark {
  position: absolute;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.08);
  animation: heroFloat 8s ease-in-out infinite;
  backdrop-filter: blur(2px);
}

.hero-shape-1 {
  width: 400px;
  height: 400px;
  top: -10%;
  right: -10%;
  animation-delay: 0s;
  background: rgba(139, 92, 246, 0.06);
}

.hero-shape-2 {
  width: 300px;
  height: 300px;
  bottom: -5%;
  left: -5%;
  animation-delay: 3s;
  background: rgba(99, 102, 241, 0.06);
}

.hero-shape-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  animation-delay: 6s;
  background: rgba(6, 182, 212, 0.06);
}

@keyframes heroFloat {
  0%,
  100% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0.6;
  }
  50% {
    transform: translate(-20px, -20px) rotate(180deg);
    opacity: 0.8;
  }
}

.min-vh-75 {
  min-height: 75vh;
}

.hero-content-dark {
  padding: 2rem 0;
}

.hero-title-dark {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.title-highlight-dark {
  background: linear-gradient(45deg, #ffd700, #ffed4e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.3));
}

.title-accent-dark {
  color: var(--text-secondary);
  font-weight: 300;
}

.hero-description-dark {
  font-size: 1.25rem;
  line-height: 1.6;
  margin-bottom: 2rem;
  color: var(--text-secondary);
}

.hero-stats-dark {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  padding: 1.5rem;
  background: rgba(30, 41, 59, 0.8);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.stat-item-dark {
  text-align: center;
}

.stat-number-dark {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ffd700, var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label-dark {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.stat-divider-dark {
  width: 2px;
  height: 40px;
  background: var(--border-color);
}

.hero-actions-dark {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.hero-btn-dark {
  padding: 1rem 2rem;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
  text-decoration: none;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-dark)
  );
  color: white;
}

.hero-btn-dark:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.4);
  color: white;
}

.hero-btn-secondary-dark {
  background: transparent;
  border: 2px solid rgba(241, 245, 249, 0.3);
  color: var(--text-primary);
}

.hero-btn-secondary-dark:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: var(--primary-color);
  color: var(--primary-light);
}

.hero-visual-dark {
  position: relative;
  height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.floating-cards-dark {
  position: relative;
  width: 100%;
  height: 100%;
}

.floating-card-dark {
  position: absolute;
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
  animation: cardFloat 6s ease-in-out infinite;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.floating-card-dark i {
  font-size: 2rem;
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

.card-1 {
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.card-2 {
  top: 50%;
  right: 20%;
  animation-delay: 2s;
}

.card-3 {
  bottom: 20%;
  left: 30%;
  animation-delay: 4s;
}

@keyframes cardFloat {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.9;
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
    opacity: 1;
  }
}

/* Dark Shows Section */
.shows-section-dark {
  padding: 5rem 0;
  background: linear-gradient(
    135deg,
    var(--bg-primary) 0%,
    var(--bg-secondary) 100%
  );
}

.section-header-dark {
  margin-bottom: 4rem;
}

.section-title-dark {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.section-description-dark {
  font-size: 1.2rem;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto;
}

.theaters-grid-dark {
  display: grid;
  gap: 2rem;
}

.theater-card-dark {
  background: var(--bg-card);
  border-radius: 20px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.theater-card-dark:hover {
  transform: translateY(-10px);
  box-shadow: var(--shadow-hover);
  border-color: rgba(139, 92, 246, 0.3);
}

.theater-header-dark {
  padding: 2rem;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--secondary-color)
  );
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.theater-name-dark {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  color: white;
}

.theater-location-dark {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  opacity: 0.9;
  display: flex;
  align-items: center;
  color: rgba(255, 255, 255, 0.9);
}

.theater-capacity-dark {
  font-size: 0.9rem;
  opacity: 0.8;
  display: flex;
  align-items: center;
  color: rgba(255, 255, 255, 0.8);
}

.theater-badge-dark .badge {
  font-size: 0.8rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.shows-grid-dark {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
}

.show-card-dark {
  background: var(--bg-card-hover);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.show-card-dark:hover {
  border-color: var(--primary-color);
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.2);
}

.show-poster-dark {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.poster-image-dark {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.show-card-dark:hover .poster-image-dark {
  transform: scale(1.05);
}

.poster-overlay-dark {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 15, 35, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.show-card-dark:hover .poster-overlay-dark {
  opacity: 1;
}

.btn-light-dark {
  background: rgba(241, 245, 249, 0.9);
  color: var(--bg-primary);
  border: none;
}

.show-info-dark {
  padding: 1.5rem;
  background: var(--bg-card);
}

.show-title-dark {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.show-details-dark {
  margin-bottom: 1rem;
}

.show-time-dark,
.show-seats-dark {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.show-status-dark {
  display: flex;
  align-items: center;
}

.availability-indicator-dark {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.availability-indicator-dark .indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.available .indicator {
  background: var(--success-color);
}

.available {
  color: var(--success-color);
}

.sold-out .indicator {
  background: var(--danger-color);
}

.sold-out {
  color: var(--danger-color);
}

.no-shows-dark {
  padding: 3rem 2rem;
  text-align: center;
  color: var(--text-muted);
}

.no-shows-dark i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.loading-state-dark {
  text-align: center;
  padding: 4rem 0;
  color: var(--text-secondary);
}

.loading-spinner-dark {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: var(--primary-color);
}

/* Dark CTA Section */
.cta-section-dark {
  padding: 5rem 0;
  background: linear-gradient(
    135deg,
    var(--bg-secondary) 0%,
    var(--bg-tertiary) 100%
  );
  color: var(--text-primary);
  border-top: 1px solid var(--border-color);
}

.cta-title-dark {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.cta-description-dark {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: var(--text-secondary);
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-btn-dark {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
  text-decoration: none;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--accent-color)
  );
  color: white;
}

.cta-btn-dark:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.4);
  color: white;
}

/* Animations */
.fade-in-up {
  animation: fadeInUp 0.8s ease-out;
  animation-fill-mode: both;
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
  .hero-title-dark {
    font-size: 2.5rem;
  }

  .hero-stats-dark {
    flex-direction: column;
    gap: 1rem;
  }

  .stat-divider-dark {
    width: 100%;
    height: 2px;
  }

  .hero-actions-dark {
    flex-direction: column;
  }

  .floating-cards-dark {
    display: none;
  }

  .section-title-dark {
    font-size: 2rem;
  }

  .shows-grid-dark {
    grid-template-columns: 1fr;
    padding: 1rem;
  }

  .theater-header-dark {
    padding: 1.5rem;
    flex-direction: column;
    gap: 1rem;
  }

  .cta-title-dark {
    font-size: 2rem;
  }
}

@media (max-width: 480px) {
  .hero-title-dark {
    font-size: 2rem;
  }

  .hero-description-dark {
    font-size: 1.1rem;
  }

  .hero-stats-dark {
    padding: 1rem;
  }

  .stat-number-dark {
    font-size: 1.5rem;
  }
}

/* Dark Mode Enhancements */
.bg-primary-dark {
  background: var(--primary-color);
}

/* Loading Animation */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.loading-spinner-dark i {
  animation: pulse 1.5s ease-in-out infinite;
}

/* Hover effects for better interactivity */
.hero-btn-dark,
.cta-btn-dark {
  position: relative;
  overflow: hidden;
}

.hero-btn-dark::before,
.cta-btn-dark::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.hero-btn-dark:hover::before,
.cta-btn-dark:hover::before {
  left: 100%;
}
</style>
