<template>
  <div class="admin-dash-dark">
    <!-- Admin Header Section -->
    <div class="admin-header-dark">
      <div class="container">
        <div class="header-content-dark">
          <div class="admin-welcome-dark">
            <h2 class="admin-title-dark">
              <i class="fas fa-shield-alt me-3"></i>
              Admin Dashboard
            </h2>
            <p class="admin-subtitle-dark">
              Manage theaters, shows, and bookings from your control center
            </p>
          </div>
          <div class="admin-actions-dark">
            <button class="btn btn-create-dark" @click="showCreateModal = true">
              <i class="fas fa-plus me-2"></i>
              Create Theater
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Statistics Section -->
    <div class="stats-section-dark">
      <div class="container">
        <div class="stats-grid-dark">
          <div class="stat-card-dark">
            <div class="stat-icon-dark">
              <i class="fas fa-building"></i>
            </div>
            <div class="stat-content-dark">
              <h3 class="stat-number-dark">{{ theaters.length }}</h3>
              <p class="stat-label-dark">Total Theaters</p>
            </div>
          </div>
          <div class="stat-card-dark">
            <div class="stat-icon-dark">
              <i class="fas fa-theater-masks"></i>
            </div>
            <div class="stat-content-dark">
              <h3 class="stat-number-dark">{{ totalShows }}</h3>
              <p class="stat-label-dark">Active Shows</p>
            </div>
          </div>
          <div class="stat-card-dark">
            <div class="stat-icon-dark">
              <i class="fas fa-users"></i>
            </div>
            <div class="stat-content-dark">
              <h3 class="stat-number-dark">{{ totalCapacity }}</h3>
              <p class="stat-label-dark">Total Capacity</p>
            </div>
          </div>
          <div class="stat-card-dark">
            <div class="stat-icon-dark">
              <i class="fas fa-ticket-alt"></i>
            </div>
            <div class="stat-content-dark">
              <h3 class="stat-number-dark">{{ totalBookings }}</h3>
              <p class="stat-label-dark">Total Bookings</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Theaters Management Section -->
    <div class="theaters-section-dark">
      <div class="container">
        <div class="section-title-dark">
          <h3>
            <i class="fas fa-cogs me-2"></i>
            Theater Management
          </h3>
        </div>

        <div class="theaters-grid-dark" v-if="theaters.length > 0">
          <div
            class="admin-theater-card-dark fade-in-up"
            v-for="(theater, index) in theaters"
            :key="index"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="theater-card-header-dark">
              <div class="theater-info-dark">
                <h4 class="theater-name-dark">
                  <i class="fas fa-building me-2"></i>
                  {{ theater.theater_name }}
                </h4>
                <p class="theater-location-dark">
                  <i class="fas fa-map-marker-alt me-2"></i>
                  {{ theater.location }}
                </p>
                <div class="theater-capacity-info-dark">
                  <i class="fas fa-users me-2"></i>
                  <span>{{ theater.capacity }} seats</span>
                </div>
              </div>
              <div class="theater-actions-dark">
                <div class="dropdown">
                  <button
                    class="btn btn-secondary-dark dropdown-toggle"
                    type="button"
                    :id="'dropdownMenuButton' + index"
                    data-bs-toggle="dropdown"
                  >
                    <i class="fas fa-ellipsis-v"></i>
                  </button>
                  <ul class="dropdown-menu dropdown-menu-dark">
                    <li>
                      <a class="dropdown-item" @click="editTheater(theater)">
                        <i class="fas fa-edit me-2"></i>Edit Theater
                      </a>
                    </li>
                    <li>
                      <a
                        class="dropdown-item"
                        @click="deleteTheater(theater.roll)"
                      >
                        <i class="fas fa-trash me-2"></i>Delete Theater
                      </a>
                    </li>
                    <li><hr class="dropdown-divider" /></li>
                    <li>
                      <a class="dropdown-item" @click="viewAnalytics(theater)">
                        <i class="fas fa-chart-bar me-2"></i>View Analytics
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div class="theater-card-body-dark">
              <div class="shows-section-header-dark">
                <h5>
                  <i class="fas fa-theater-masks me-2"></i>
                  Shows ({{ theater.shows ? theater.shows.length : 0 }})
                </h5>
                <button class="btn btn-add-show-dark" @click="addShow(theater)">
                  <i class="fas fa-plus me-1"></i>
                  Add Show
                </button>
              </div>

              <div
                class="shows-list-dark"
                v-if="theater.shows && theater.shows.length > 0"
              >
                <div
                  class="show-item-dark"
                  v-for="(show, showIndex) in theater.shows"
                  :key="showIndex"
                >
                  <div class="show-poster-mini-dark">
                    <img
                      :src="posterImg(show.show_name)"
                      :alt="show.show_name"
                      class="poster-mini-image-dark"
                    />
                  </div>
                  <div class="show-details-dark">
                    <h6 class="show-name-dark">{{ show.show_name }}</h6>
                    <div class="show-info-row-dark">
                      <span class="show-time-dark">
                        <i class="fas fa-clock me-1"></i>
                        {{ show.time }}
                      </span>
                      <span class="show-bookings-dark">
                        <i class="fas fa-users me-1"></i>
                        {{ show.seats_booked }}/{{ theater.capacity }}
                      </span>
                    </div>
                    <div class="show-status-dark">
                      <div
                        class="status-badge-dark"
                        :class="
                          getShowStatus(theater.capacity, show.seats_booked)
                        "
                      >
                        {{
                          getShowStatusText(theater.capacity, show.seats_booked)
                        }}
                      </div>
                    </div>
                  </div>
                  <div class="show-actions-dark">
                    <button
                      class="btn btn-edit-show-dark"
                      @click="editShow(theater, show)"
                    >
                      <i class="fas fa-edit"></i>
                    </button>
                    <button
                      class="btn btn-delete-show-dark"
                      @click="deleteShow(theater.roll, show.roll)"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>

              <div class="no-shows-admin-dark" v-else>
                <i class="fas fa-calendar-times"></i>
                <p>No shows scheduled</p>
                <button
                  class="btn btn-primary-dark btn-sm"
                  @click="addShow(theater)"
                >
                  <i class="fas fa-plus me-1"></i>
                  Add First Show
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="empty-state-dark" v-else>
          <div class="empty-icon-dark">
            <i class="fas fa-building"></i>
          </div>
          <h4>No Theaters Found</h4>
          <p>Get started by creating your first theater</p>
          <button class="btn btn-primary-dark" @click="showCreateModal = true">
            <i class="fas fa-plus me-2"></i>
            Create First Theater
          </button>
        </div>
      </div>
    </div>

    <!-- Create Theater Modal -->
    <div
      class="modal fade"
      id="createTheaterModal"
      v-if="showCreateModal"
      tabindex="-1"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content modal-content-dark">
          <div class="modal-header modal-header-dark">
            <h5 class="modal-title">
              <i class="fas fa-plus me-2"></i>
              Create New Theater
            </h5>
            <button
              type="button"
              class="btn-close btn-close-dark"
              @click="showCreateModal = false"
            ></button>
          </div>
          <div class="modal-body modal-body-dark">
            <form @submit.prevent="createTheater">
              <div class="form-group-dark mb-3">
                <label class="form-label-dark">Theater Name</label>
                <input
                  type="text"
                  class="form-control-dark"
                  v-model="newTheater.name"
                  placeholder="Enter theater name"
                  required
                />
              </div>
              <div class="form-group-dark mb-3">
                <label class="form-label-dark">Location</label>
                <input
                  type="text"
                  class="form-control-dark"
                  v-model="newTheater.location"
                  placeholder="Enter theater location"
                  required
                />
              </div>
              <div class="form-group-dark mb-3">
                <label class="form-label-dark">Capacity</label>
                <input
                  type="number"
                  class="form-control-dark"
                  v-model="newTheater.capacity"
                  placeholder="Enter seating capacity"
                  min="1"
                  required
                />
              </div>
            </form>
          </div>
          <div class="modal-footer modal-footer-dark">
            <button
              type="button"
              class="btn btn-secondary-dark"
              @click="showCreateModal = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn btn-primary-dark"
              @click="createTheater"
            >
              <i class="fas fa-save me-2"></i>
              Create Theater
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "AdminDashPage",
  data() {
    return {
      theaters: [],
      formData: {
        theater_name: "",
        location: "",
        capacity: "",
      },
      userSession: JSON.parse(localStorage.getItem("userSession")) || null,
      showCreateModal: false,
      newTheater: {
        name: "",
        location: "",
        capacity: "",
      },
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

    async addTheaterForm() {
      try {
        if (this.userSession && this.userSession.token) {
          // Set the Authorization header with the JWT token
          axios.defaults.headers.common[
            "Authorization"
          ] = `Bearer ${this.userSession.token}`;
          const formData = new FormData();
          formData.append("theater_name", this.formData.theater_name);
          formData.append("location", this.formData.location);
          formData.append("capacity", this.formData.capacity);

          const response = await axios.post(
            "http://127.0.0.1:1234/vue/theater",
            formData
          );
          console.log("User Token:", this.userSession.token);
          console.log(response);
          this.getTheater();
        } else {
          // Handle the case where the user is not authenticated
          console.error("User is not authenticated.");
          // You can redirect to the login page or show an error message here
        }
      } catch (error) {
        console.error("AxiosError:", error);
        console.log(this.userSession.token);

        if (error.response) {
          console.error("Response Data:", error.response.data);
        } else {
          console.error("Network Error:", error.message);
        }
        alert("Oops! An error occurred. Theater was not added.");
      }
    },
    deleteTheater(theater_id) {
      try {
        if (this.userSession && this.userSession.token) {
          // Set the Authorization header with the JWT token
          axios.defaults.headers.common[
            "Authorization"
          ] = `Bearer ${this.userSession.token}`;
          const response = axios.delete(
            `http://127.0.0.1:1234/vue/theater/${theater_id}`
          );
          console.log(response);
          alert("Theater deleted Successfully");
          this.getTheater();
        } else {
          // Handle the case where the user is not authenticated
          console.error("User is not authenticated.");
          // You can redirect to the login page or show an error message here
        }
      } catch (error) {
        console.error("AxiosError:", error);
        if (error.response) {
          console.error("Response Data:", error.response.data);
        } else {
          console.error("Network Error:", error.message);
        }
        alert("Oops! An error occurred. Theater was not deleted.");
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
    getShowStatus(totalCapacity, seatsBooked) {
      if (seatsBooked >= totalCapacity) {
        return "sold-out";
      } else if (seatsBooked >= totalCapacity * 0.7) {
        return "limited";
      } else {
        return "available";
      }
    },
    getShowStatusText(totalCapacity, seatsBooked) {
      if (seatsBooked >= totalCapacity) {
        return "Sold Out";
      } else if (seatsBooked >= totalCapacity * 0.7) {
        return "Limited Availability";
      } else {
        return "Available";
      }
    },
    editTheater(theater) {
      this.formData.theater_name = theater.theater_name;
      this.formData.location = theater.location;
      this.formData.capacity = theater.capacity;
      this.$refs.theaterModal.show();
    },
    async createTheater() {
      try {
        if (this.userSession && this.userSession.token) {
          axios.defaults.headers.common[
            "Authorization"
          ] = `Bearer ${this.userSession.token}`;
          const response = await axios.post(
            "http://127.0.0.1:1234/vue/theater",
            this.newTheater
          );
          console.log(response);
          alert("Theater created successfully!");
          this.getTheater();
          this.showCreateModal = false;
          this.newTheater = { name: "", location: "", capacity: "" };
        } else {
          alert("User not authenticated. Please log in.");
        }
      } catch (error) {
        console.error("AxiosError:", error);
        if (error.response) {
          console.error("Response Data:", error.response.data);
        } else {
          console.error("Network Error:", error.message);
        }
        alert("Oops! An error occurred. Theater was not created.");
      }
    },
    editShow(theater, show) {
      this.$router.push({ name: "admin-edit-show", params: { id: show.roll } });
    },
    async deleteShow(theaterId, showId) {
      try {
        if (this.userSession && this.userSession.token) {
          axios.defaults.headers.common["Authorization"] = `Bearer ${this.userSession.token}`;
          await axios.delete(`http://127.0.0.1:1234/vue/show/${showId}`);
          alert("Show deleted Successfully");
          this.getTheater();
        } else {
          alert("User not authenticated. Please log in.");
        }
      } catch (error) {
        console.error("AxiosError:", error);
        if (error.response) {
          console.error("Response Data:", error.response.data);
        } else {
          console.error("Network Error:", error.message);
        }
        alert("Oops! An error occurred. Show was not deleted.");
      }
    },
    addShow(theater) {
      this.$router.push({ name: "admin-add-show", params: { id: theater.roll } });
    },
    viewAnalytics(theater) {
      this.$router.push({ name: "analytics", params: { id: theater.roll } });
    },
  },
  async created() {
    await this.getTheater();
    await this.loadShowsForTheaters();
    const fetchData = async () => {
      try {
        await this.getTheater();
        await this.loadShowsForTheaters();
      } catch (error) {
        console.error("Error fetching theaters:", error);
      }
    };
    fetchData();

    setInterval(fetchData, 60000);
  },
};
</script>

<style scoped>
.admin-dash-dark {
  min-height: calc(100vh - 200px);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.admin-header-dark {
  background: linear-gradient(
    135deg,
    var(--bg-secondary) 0%,
    var(--bg-tertiary) 100%
  );
  padding: 3rem 0;
  border-bottom: 1px solid var(--border-color);
}

.header-content-dark {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-title-dark {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.admin-title-dark i {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--accent-color)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.admin-subtitle-dark {
  font-size: 1.2rem;
  color: var(--text-secondary);
  margin: 0;
}

.btn-create-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-dark)
  );
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: var(--border-radius);
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-create-dark:hover {
  background: linear-gradient(135deg, var(--primary-dark), var(--accent-color));
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(139, 92, 246, 0.3);
  color: white;
}

.stats-section-dark {
  padding: 3rem 0;
  background: var(--bg-primary);
}

.stats-grid-dark {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.stat-card-dark {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: 2rem;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: all 0.3s ease;
}

.stat-card-dark:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-hover);
  border-color: rgba(139, 92, 246, 0.3);
}

.stat-icon-dark {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--accent-color)
  );
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
  flex-shrink: 0;
}

.stat-number-dark {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.stat-label-dark {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
}

.theaters-section-dark {
  padding: 3rem 0;
  background: linear-gradient(
    135deg,
    var(--bg-primary) 0%,
    var(--bg-secondary) 100%
  );
}

.section-title-dark h3 {
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
}

.theaters-grid-dark {
  display: grid;
  gap: 2rem;
}

.admin-theater-card-dark {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.admin-theater-card-dark:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-hover);
  border-color: rgba(139, 92, 246, 0.3);
}

.theater-card-header-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--secondary-color)
  );
  padding: 2rem;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.theater-name-dark {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: white;
}

.theater-location-dark {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
}

.theater-capacity-info-dark {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.btn-secondary-dark {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dropdown-menu-dark {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-card);
}

.dropdown-item {
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.dropdown-item:hover {
  background: var(--bg-card-hover);
  color: var(--primary-light);
}

.theater-card-body-dark {
  padding: 2rem;
  background: var(--bg-card);
}

.shows-section-header-dark {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.shows-section-header-dark h5 {
  color: var(--text-primary);
  margin: 0;
}

.btn-add-show-dark {
  background: linear-gradient(
    135deg,
    var(--success-color),
    var(--success-dark)
  );
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--border-radius);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-add-show-dark:hover {
  background: linear-gradient(
    135deg,
    var(--success-dark),
    var(--success-color)
  );
  transform: translateY(-2px);
  box-shadow: 0 3px 10px rgba(16, 185, 129, 0.3);
  color: white;
}

.shows-list-dark {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.show-item-dark {
  background: var(--bg-card-hover);
  border-radius: var(--border-radius);
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.show-item-dark:hover {
  border-color: var(--primary-color);
  box-shadow: 0 3px 10px rgba(139, 92, 246, 0.1);
}

.show-poster-mini-dark {
  width: 60px;
  height: 80px;
  border-radius: var(--border-radius);
  overflow: hidden;
  flex-shrink: 0;
}

.poster-mini-image-dark {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.show-details-dark {
  flex: 1;
}

.show-name-dark {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.show-info-row-dark {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.show-time-dark,
.show-bookings-dark {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.status-badge-dark {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge-dark.available {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success-color);
}

.status-badge-dark.limited {
  background: rgba(245, 158, 11, 0.2);
  color: var(--warning-color);
}

.status-badge-dark.sold-out {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger-color);
}

.show-actions-dark {
  display: flex;
  gap: 0.5rem;
}

.btn-edit-show-dark,
.btn-delete-show-dark {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  transition: all 0.3s ease;
}

.btn-edit-show-dark {
  background: rgba(59, 130, 246, 0.2);
  color: var(--info-color);
}

.btn-edit-show-dark:hover {
  background: var(--info-color);
  color: white;
  transform: scale(1.1);
}

.btn-delete-show-dark {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger-color);
}

.btn-delete-show-dark:hover {
  background: var(--danger-color);
  color: white;
  transform: scale(1.1);
}

.no-shows-admin-dark {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--text-muted);
}

.no-shows-admin-dark i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state-dark {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
}

.empty-icon-dark {
  font-size: 4rem;
  margin-bottom: 2rem;
  opacity: 0.5;
}

.empty-state-dark h4 {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

/* Modal Dark Theme */
.modal-content-dark {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
}

.modal-header-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--secondary-color)
  );
  color: white;
  border-bottom: 1px solid var(--border-color);
}

.modal-header-dark .modal-title {
  color: white;
}

.btn-close-dark {
  filter: invert(1);
}

.modal-body-dark {
  background: var(--bg-card);
  color: var(--text-primary);
}

.form-group-dark {
  margin-bottom: 1rem;
}

.form-label-dark {
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 0.5rem;
  display: block;
}

.form-control-dark {
  background: var(--bg-card-hover);
  border: 2px solid var(--border-color);
  color: var(--text-primary);
  border-radius: var(--border-radius);
  padding: 0.75rem 1rem;
  width: 100%;
  transition: all 0.3s ease;
}

.form-control-dark::placeholder {
  color: var(--text-muted);
}

.form-control-dark:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  background: var(--bg-card);
  outline: none;
}

.modal-footer-dark {
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
}

.btn-primary-dark {
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-dark)
  );
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: var(--border-radius);
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary-dark:hover {
  background: linear-gradient(135deg, var(--primary-dark), var(--accent-color));
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(139, 92, 246, 0.3);
  color: white;
}

.btn-secondary-dark {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  padding: 0.75rem 1.5rem;
  border-radius: var(--border-radius);
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-secondary-dark:hover {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-light);
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
  .header-content-dark {
    flex-direction: column;
    gap: 2rem;
    text-align: center;
  }

  .admin-title-dark {
    font-size: 2rem;
  }

  .stats-grid-dark {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .stat-card-dark {
    padding: 1.5rem;
  }

  .theater-card-header-dark {
    flex-direction: column;
    gap: 1rem;
    padding: 1.5rem;
  }

  .theater-card-body-dark {
    padding: 1.5rem;
  }

  .shows-section-header-dark {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .show-item-dark {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .show-info-row-dark {
    flex-direction: column;
    gap: 0.5rem;
  }
}

@media (max-width: 480px) {
  .admin-header-dark {
    padding: 2rem 0;
  }

  .admin-title-dark {
    font-size: 1.8rem;
  }

  .stats-section-dark,
  .theaters-section-dark {
    padding: 2rem 0;
  }

  .stat-card-dark {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .stat-icon-dark {
    width: 50px;
    height: 50px;
    font-size: 1.2rem;
  }
}

/* Additional enhancements */
.admin-theater-card-dark::before {
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

.admin-theater-card-dark:hover::before {
  transform: scaleX(1);
}

/* Loading states */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 15, 35, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-size: 2rem;
}
</style>
