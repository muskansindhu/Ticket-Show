<template>
  <div class="user-dash-dark">
    <div class="welcome-section-dark">
      <div class="container">
        <div class="welcome-header-dark text-center">
          <h2 class="welcome-title-dark">
            <i class="fas fa-star me-3"></i>
            Welcome to TicketShow
          </h2>
          <p class="welcome-subtitle-dark">
            Your one-stop destination for booking amazing shows
          </p>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="row justify-content-center">
        <div
          class="col-md-10"
          v-for="(theater, index) in theaters"
          :key="index"
        >
          <div
            class="theater-card-dark mb-4 fade-in-up"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="theater-header-dark">
              <div class="theater-info-section-dark">
                <div class="theater-details-dark">
                  <h5 class="theater-title-dark">
                    <i class="fas fa-building me-2"></i>
                    {{ theater.theater_name }}
                  </h5>
                  <p class="theater-location-dark">
                    <i class="fas fa-map-marker-alt me-2"></i>
                    {{ theater.location }}
                  </p>
                  <div class="theater-capacity-dark">
                    <i class="fas fa-users me-2"></i>
                    <strong>Capacity:</strong> {{ theater.capacity }} seats
                  </div>
                </div>
                <div class="theater-badge-dark">
                  <span class="badge bg-premium-dark">
                    <i class="fas fa-crown me-1"></i>
                    Premium Theater
                  </span>
                </div>
              </div>
            </div>

            <div class="theater-body-dark">
              <!-- Show cards -->
              <div
                class="shows-grid-dark"
                v-if="theater.shows && theater.shows.length > 0"
              >
                <div
                  class="show-card-dark"
                  v-for="(show, showIndex) in theater.shows"
                  :key="showIndex"
                >
                  <div class="show-poster-section-dark">
                    <img
                      :src="posterImg(show.show_name)"
                      alt="Show Poster"
                      class="show-poster-image-dark"
                    />
                    <div class="show-overlay-dark">
                      <div class="show-rating-dark">
                        <i class="fas fa-star"></i>
                        <span>4.8</span>
                      </div>
                    </div>
                  </div>

                  <div class="show-content-dark">
                    <h6 class="show-name-dark">{{ show.show_name }}</h6>
                    <div class="show-details-dark">
                      <div class="show-time-dark">
                        <i class="fas fa-clock me-2"></i>
                        <strong>Show Time:</strong> {{ show.time }}
                      </div>
                      <div class="show-availability-dark">
                        <i class="fas fa-chair me-2"></i>
                        <strong>Available Seats:</strong>
                        <span class="seats-count-dark">
                          {{
                            availableSeats(theater.capacity, show.seats_booked)
                          }}
                        </span>
                      </div>
                    </div>

                    <div class="show-actions-dark">
                      <template
                        v-if="
                          availableSeats(theater.capacity, show.seats_booked) >
                          0
                        "
                      >
                        <a
                          :href="'/show/' + show.roll + '/booking'"
                          class="btn btn-book-dark"
                        >
                          <i class="fas fa-ticket-alt me-2"></i>
                          Book Now
                        </a>
                        <div class="availability-status-dark available">
                          <span class="status-indicator-dark"></span>
                          Available
                        </div>
                      </template>
                      <template v-else>
                        <button class="btn btn-sold-out-dark" disabled>
                          <i class="fas fa-times-circle me-2"></i>
                          Sold Out
                        </button>
                        <div class="availability-status-dark sold-out">
                          <span class="status-indicator-dark"></span>
                          House Full
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
              </div>

              <div class="no-shows-message-dark" v-else>
                <div class="no-shows-icon-dark">
                  <i class="fas fa-calendar-times"></i>
                </div>
                <h6>No Shows Available</h6>
                <p>
                  This theater currently has no scheduled shows. Check back
                  later for updates!
                </p>
              </div>
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
  name: "UserDashPage",
  data() {
    return {
      theaters: [],
      formData: {
        theater_name: "",
        location: "",
        capacity: "",
      },
      userSession: JSON.parse(localStorage.getItem("userSession")) || null,
    };
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

    loadShowsForTheaters() {
      for (const theater of this.theaters) {
        this.getShowsForTheater(theater);
      }
    },
    posterImg(showName) {
      return `http://127.0.0.1:1234/static/img/Posters/${showName}.webp`;
    },
    availableSeats(theaterCapacity, showSeatsBooked) {
      return theaterCapacity - showSeatsBooked;
    },
  },
  async created() {
    await this.getTheater();
  },
};
</script>

<style scoped>
.user-dash-dark {
  min-height: calc(100vh - 200px);
  background: var(--bg-primary);
  color: var(--text-primary);
  padding: 2rem 0;
}

.welcome-section-dark {
  background: linear-gradient(
    135deg,
    var(--bg-secondary) 0%,
    var(--bg-tertiary) 100%
  );
  padding: 3rem 0;
  margin-bottom: 3rem;
  border-bottom: 1px solid var(--border-color);
}

.welcome-header-dark {
  max-width: 600px;
  margin: 0 auto;
}

.welcome-title-dark {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.welcome-title-dark i {
  background: linear-gradient(135deg, #ffd700, var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle-dark {
  font-size: 1.2rem;
  color: var(--text-secondary);
  margin: 0;
}

.theater-card-dark {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.theater-card-dark:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-hover);
  border-color: rgba(139, 92, 246, 0.3);
}

.theater-header-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  padding: 2rem;
  color: white;
}

.theater-info-section-dark {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.theater-details-dark {
  flex: 1;
}

.theater-title-dark {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: white;
  display: flex;
  align-items: center;
}

.theater-location-dark {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
}

.theater-capacity-dark {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
}

.theater-badge-dark {
  flex-shrink: 0;
}

.bg-premium-dark {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  border: 1px solid rgba(255, 215, 0, 0.3);
  padding: 0.5rem 1rem;
  border-radius: 25px;
  font-weight: 600;
  font-size: 0.85rem;
}

.theater-body-dark {
  padding: 2rem;
  background: var(--bg-card);
}

.shows-grid-dark {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.show-card-dark {
  background: var(--bg-card-hover);
  border-radius: var(--border-radius);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.show-card-dark:hover {
  transform: translateY(-5px);
  border-color: var(--primary-color);
  box-shadow: 0 8px 25px rgba(139, 92, 246, 0.2);
}

.show-poster-section-dark {
  position: relative;
  height: 250px;
  overflow: hidden;
}

.show-poster-image-dark {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.show-card-dark:hover .show-poster-image-dark {
  transform: scale(1.05);
}

.show-overlay-dark {
  position: absolute;
  top: 0;
  right: 0;
  padding: 1rem;
}

.show-rating-dark {
  background: rgba(0, 0, 0, 0.7);
  color: #ffd700;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.show-content-dark {
  padding: 1.5rem;
  background: var(--bg-card-hover);
}

.show-name-dark {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  text-align: center;
}

.show-details-dark {
  margin-bottom: 1.5rem;
}

.show-time-dark,
.show-availability-dark {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.seats-count-dark {
  color: var(--success-color);
  font-weight: 600;
}

.show-actions-dark {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
}

.btn-book-dark {
  background: linear-gradient(
    135deg,
    var(--success-color),
    var(--success-dark)
  );
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: var(--border-radius);
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  min-width: 140px;
  justify-content: center;
}

.btn-book-dark:hover {
  background: linear-gradient(
    135deg,
    var(--success-dark),
    var(--success-color)
  );
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(16, 185, 129, 0.3);
  color: white;
}

.btn-sold-out-dark {
  background: linear-gradient(135deg, var(--danger-color), var(--danger-dark));
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: var(--border-radius);
  font-weight: 600;
  cursor: not-allowed;
  opacity: 0.8;
  display: flex;
  align-items: center;
  min-width: 140px;
  justify-content: center;
}

.availability-status-dark {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.status-indicator-dark {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.availability-status-dark.available {
  color: var(--success-color);
}

.availability-status-dark.available .status-indicator-dark {
  background: var(--success-color);
}

.availability-status-dark.sold-out {
  color: var(--danger-color);
}

.availability-status-dark.sold-out .status-indicator-dark {
  background: var(--danger-color);
}

.no-shows-message-dark {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
}

.no-shows-icon-dark {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  opacity: 0.5;
}

.no-shows-message-dark h6 {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.no-shows-message-dark p {
  font-size: 1rem;
  color: var(--text-muted);
  max-width: 400px;
  margin: 0 auto;
}

/* Animation */
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
  .welcome-title-dark {
    font-size: 2rem;
  }

  .welcome-subtitle-dark {
    font-size: 1.1rem;
  }

  .theater-header-dark {
    padding: 1.5rem;
  }

  .theater-info-section-dark {
    flex-direction: column;
    gap: 1rem;
  }

  .theater-body-dark {
    padding: 1.5rem;
  }

  .shows-grid-dark {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .show-poster-section-dark {
    height: 200px;
  }
}

@media (max-width: 480px) {
  .user-dash-dark {
    padding: 1rem 0;
  }

  .welcome-section-dark {
    padding: 2rem 0;
    margin-bottom: 2rem;
  }

  .welcome-title-dark {
    font-size: 1.8rem;
  }

  .theater-card-dark {
    margin: 0 1rem 2rem;
  }

  .theater-header-dark,
  .theater-body-dark {
    padding: 1rem;
  }
}

/* Loading states */
.show-card-dark.loading {
  position: relative;
  overflow: hidden;
}

.show-card-dark.loading::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(139, 92, 246, 0.1),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

/* Hover effects enhancement */
.theater-card-dark::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--accent-color)
  );
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.theater-card-dark:hover::before {
  transform: scaleX(1);
}

/* Accessibility improvements */
.btn-book-dark:focus,
.btn-sold-out-dark:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.show-card-dark:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}
</style>
