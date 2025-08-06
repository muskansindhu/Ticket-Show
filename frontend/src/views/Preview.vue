<template>
  <div class="preview-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-background">
        <div class="hero-overlay"></div>
        <div class="hero-shapes">
          <div class="hero-shape hero-shape-1"></div>
          <div class="hero-shape hero-shape-2"></div>
          <div class="hero-shape hero-shape-3"></div>
        </div>
      </div>

      <div class="container">
        <div class="row align-items-center min-vh-75">
          <div class="col-lg-6">
            <div class="hero-content">
              <h1 class="hero-title">
                <span class="title-highlight">Premium</span>
                Entertainment
                <br />
                <span class="title-accent">Awaits You</span>
              </h1>
              <p class="hero-description">
                Discover and book the most exciting shows, theaters, and
                entertainment experiences. Your gateway to unforgettable moments
                starts here.
              </p>
              <div class="hero-stats">
                <div class="stat-item">
                  <div class="stat-number">{{ theaters.length }}+</div>
                  <div class="stat-label">Theaters</div>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-item">
                  <div class="stat-number">{{ totalShows }}+</div>
                  <div class="stat-label">Shows</div>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-item">
                  <div class="stat-number">1000+</div>
                  <div class="stat-label">Happy Customers</div>
                </div>
              </div>
              <div class="hero-actions">
                <router-link
                  to="/login"
                  class="btn btn-primary btn-lg hero-btn"
                >
                  <i class="fas fa-ticket-alt me-2"></i>
                  Get Started
                </router-link>
                <button
                  class="btn btn-outline-light btn-lg hero-btn-secondary"
                  @click="scrollToShows"
                >
                  <i class="fas fa-play-circle me-2"></i>
                  Explore Shows
                </button>
              </div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="hero-visual">
              <div class="floating-cards">
                <div class="floating-card card-1">
                  <i class="fas fa-theater-masks"></i>
                  <span>Drama</span>
                </div>
                <div class="floating-card card-2">
                  <i class="fas fa-music"></i>
                  <span>Musical</span>
                </div>
                <div class="floating-card card-3">
                  <i class="fas fa-laugh"></i>
                  <span>Comedy</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Shows Section -->
    <section class="shows-section" id="shows">
      <div class="container">
        <div class="section-header text-center">
          <h2 class="section-title">
            <span class="title-accent">Featured</span> Shows & Theaters
          </h2>
          <p class="section-description">
            Discover amazing entertainment options across our premium theater
            network
          </p>
        </div>

        <div class="theaters-grid" v-if="theaters.length > 0">
          <div
            class="theater-card fade-in-up"
            v-for="(theater, index) in theaters"
            :key="index"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="theater-header">
              <div class="theater-info">
                <h3 class="theater-name">
                  <i class="fas fa-building me-2"></i>
                  {{ theater.theater_name }}
                </h3>
                <p class="theater-location">
                  <i class="fas fa-map-marker-alt me-2"></i>
                  {{ theater.location }}
                </p>
                <div class="theater-capacity">
                  <i class="fas fa-users me-2"></i>
                  <span>Capacity: {{ theater.capacity }} seats</span>
                </div>
              </div>
              <div class="theater-badge">
                <span class="badge bg-primary">Premium</span>
              </div>
            </div>

            <div
              class="shows-grid"
              v-if="theater.shows && theater.shows.length > 0"
            >
              <div
                class="show-card"
                v-for="(show, showIndex) in theater.shows"
                :key="showIndex"
              >
                <div class="show-poster">
                  <img
                    :src="posterImg(show.show_name)"
                    :alt="show.show_name"
                    class="poster-image"
                    @error="handleImageError"
                  />
                  <div class="poster-overlay">
                    <div class="show-actions">
                      <button class="btn btn-sm btn-light" disabled>
                        <i class="fas fa-eye me-1"></i>
                        Preview
                      </button>
                    </div>
                  </div>
                </div>

                <div class="show-info">
                  <h4 class="show-title">{{ show.show_name }}</h4>
                  <div class="show-details">
                    <div class="show-time">
                      <i class="fas fa-clock me-2"></i>
                      {{ formatTime(show.time) }}
                    </div>
                    <div class="show-seats">
                      <i class="fas fa-chair me-2"></i>
                      {{ availableSeats(theater.capacity, show.seats_booked) }}
                      available
                    </div>
                  </div>

                  <div class="show-status">
                    <template
                      v-if="
                        availableSeats(theater.capacity, show.seats_booked) > 0
                      "
                    >
                      <div class="availability-indicator available">
                        <span class="indicator"></span>
                        Available
                      </div>
                    </template>
                    <template v-else>
                      <div class="availability-indicator sold-out">
                        <span class="indicator"></span>
                        Sold Out
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <div class="no-shows" v-else>
              <i class="fas fa-calendar-times"></i>
              <p>No shows currently scheduled</p>
            </div>
          </div>
        </div>

        <div class="loading-state" v-else>
          <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
          </div>
          <p>Loading amazing shows...</p>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-content text-center">
          <h2 class="cta-title">Ready to Experience Something Amazing?</h2>
          <p class="cta-description">
            Join thousands of entertainment lovers and never miss a great show
            again.
          </p>
          <router-link to="/login" class="btn btn-primary btn-lg cta-btn">
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
.preview-page {
  overflow-x: hidden;
}

/* Hero Section */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  color: white;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: -1;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
}

.hero-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.hero-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: heroFloat 8s ease-in-out infinite;
}

.hero-shape-1 {
  width: 400px;
  height: 400px;
  top: -10%;
  right: -10%;
  animation-delay: 0s;
}

.hero-shape-2 {
  width: 300px;
  height: 300px;
  bottom: -5%;
  left: -5%;
  animation-delay: 3s;
}

.hero-shape-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  animation-delay: 6s;
}

@keyframes heroFloat {
  0%,
  100% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0.1;
  }
  50% {
    transform: translate(-20px, -20px) rotate(180deg);
    opacity: 0.2;
  }
}

.min-vh-75 {
  min-height: 75vh;
}

.hero-content {
  padding: 2rem 0;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 1.5rem;
}

.title-highlight {
  background: linear-gradient(45deg, #ffd700, #ffed4e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-accent {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 300;
}

.hero-description {
  font-size: 1.25rem;
  line-height: 1.6;
  margin-bottom: 2rem;
  color: rgba(255, 255, 255, 0.9);
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #ffd700;
}

.stat-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.stat-divider {
  width: 2px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
}

.hero-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.hero-btn {
  padding: 1rem 2rem;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
  text-decoration: none;
}

.hero-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.hero-btn-secondary {
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.5);
  color: white;
}

.hero-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: white;
  color: white;
}

.hero-visual {
  position: relative;
  height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.floating-cards {
  position: relative;
  width: 100%;
  height: 100%;
}

.floating-card {
  position: absolute;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: white;
  animation: cardFloat 6s ease-in-out infinite;
}

.floating-card i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
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
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
  }
}

/* Shows Section */
.shows-section {
  padding: 5rem 0;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.section-header {
  margin-bottom: 4rem;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #2d3748;
}

.section-description {
  font-size: 1.2rem;
  color: #718096;
  max-width: 600px;
  margin: 0 auto;
}

.theaters-grid {
  display: grid;
  gap: 2rem;
}

.theater-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.theater-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.theater-header {
  padding: 2rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.theater-name {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
}

.theater-location {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  opacity: 0.9;
  display: flex;
  align-items: center;
}

.theater-capacity {
  font-size: 0.9rem;
  opacity: 0.8;
  display: flex;
  align-items: center;
}

.theater-badge .badge {
  font-size: 0.8rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
}

.shows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
}

.show-card {
  background: #f8fafc;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.show-card:hover {
  border-color: #667eea;
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.15);
}

.show-poster {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.poster-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.show-card:hover .poster-image {
  transform: scale(1.05);
}

.poster-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.show-card:hover .poster-overlay {
  opacity: 1;
}

.show-info {
  padding: 1.5rem;
}

.show-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2d3748;
}

.show-details {
  margin-bottom: 1rem;
}

.show-time,
.show-seats {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: #718096;
  margin-bottom: 0.5rem;
}

.show-status {
  display: flex;
  align-items: center;
}

.availability-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.availability-indicator .indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.available .indicator {
  background: #48bb78;
}

.available {
  color: #48bb78;
}

.sold-out .indicator {
  background: #f56565;
}

.sold-out {
  color: #f56565;
}

.no-shows {
  padding: 3rem 2rem;
  text-align: center;
  color: #a0aec0;
}

.no-shows i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.loading-state {
  text-align: center;
  padding: 4rem 0;
  color: #718096;
}

.loading-spinner {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #667eea;
}

/* CTA Section */
.cta-section {
  padding: 5rem 0;
  background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
  color: white;
}

.cta-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.cta-description {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-btn {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
  text-decoration: none;
}

.cta-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
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
  .hero-title {
    font-size: 2.5rem;
  }

  .hero-stats {
    flex-direction: column;
    gap: 1rem;
  }

  .stat-divider {
    width: 100%;
    height: 2px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .floating-cards {
    display: none;
  }

  .section-title {
    font-size: 2rem;
  }

  .shows-grid {
    grid-template-columns: 1fr;
    padding: 1rem;
  }

  .theater-header {
    padding: 1.5rem;
    flex-direction: column;
    gap: 1rem;
  }

  .cta-title {
    font-size: 2rem;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2rem;
  }

  .hero-description {
    font-size: 1.1rem;
  }

  .hero-stats {
    padding: 1rem;
  }

  .stat-number {
    font-size: 1.5rem;
  }
}
</style>
