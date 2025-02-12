import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------
# 1. MODEL PARAMETERS
# ---------------------------------------------------

# Simulation time
total_hours = 24
dt_minutes = 1          # Time step in minutes
dt = dt_minutes / 60.0  # Time step in hours
num_steps = int(total_hours / dt)

# Room parameters
room_volume = 30.0  # m^3  (example)
vent_rate = 3.0     # Air changes per hour (ACH) for the entire space

# Infectious aerosol generation
quanta_generation_rate = 10.0  # quanta/hour per infectious person
# This is an adjustable parameter and depends on activities (talking, etc.)

# Other decay mechanisms (e.g. deposition, inactivation)
# Summarize them as an overall "decay" rate in air in h^-1
decay_rate = 0.3

# Prevalence of infectious individuals
prevalence = 0.02  # 2% of population is infectious

# People arrival parameters
mean_arrivals_per_hour = 10   # average arrivals per hour
mean_time_spent_minutes = 5.0 # average time spent in toilet
# Adjust these as appropriate for your scenario

# Random seed for reproducibility
np.random.seed(42)

# ---------------------------------------------------
# 2. ARRIVALS & OCCUPANCY SCHEDULE
# ---------------------------------------------------
# We’ll create a schedule of arrivals for the 24h period.
# For each arrival, we store:
#   arrival_time (in minutes)
#   dwell_time (in minutes)
#   infectious (bool)
#   occupant ID
#
# Then, as the simulation steps through time, we check who is present.

def generate_arrivals(total_hours, mean_arrivals_per_hour, 
                      mean_time_spent_minutes, prevalence):
    """
    Returns a list of dicts with occupant info:
      - occupant_id
      - arrival_time (minutes)
      - dwell_time (minutes)
      - infectious (bool)
    """
    total_minutes = total_hours * 60
    arrivals = []
    
    # Poisson process for arrivals:
    # We can sample the number of arrivals for each hour from a Poisson,
    # or do a single Poisson for the entire day. 
    # Then we randomize arrival times across the day.
    # For simplicity, let's do a single Poisson for the 24h total.
    
    lambda_24h = mean_arrivals_per_hour * 24  # expected arrivals in 24h
    num_arrivals = np.random.poisson(lambda_24h) 
    
    for i in range(num_arrivals):
        # random arrival time in minutes (uniform over 24h for now,
        # though you may want a time-varying rate for busy/quiet times)
        arrival_t = np.random.uniform(0, total_minutes)
        
        # sample dwell time from, e.g., an exponential distribution
        # or a lognormal. We'll use exponential for demonstration
        dwell_t = np.random.exponential(mean_time_spent_minutes)
        
        # determine if infectious
        is_infectious = (np.random.rand() < prevalence)
        
        occupant_info = {
            'occupant_id': i,
            'arrival_time': arrival_t,
            'dwell_time': dwell_t,
            'infectious': is_infectious
        }
        arrivals.append(occupant_info)
    
    # sort by arrival time
    arrivals = sorted(arrivals, key=lambda x: x['arrival_time'])
    
    return arrivals

arrivals = generate_arrivals(
    total_hours=total_hours,
    mean_arrivals_per_hour=mean_arrivals_per_hour,
    mean_time_spent_minutes=mean_time_spent_minutes,
    prevalence=prevalence
)

# For tracking occupant dose, we’ll need a data structure to store 
# the cumulative inhaled dose (quanta) for each occupant.
occupant_dose = { a['occupant_id']: 0.0 for a in arrivals }

# ---------------------------------------------------
# 3. PREPARE FOR SIMULATION
# ---------------------------------------------------

# Convert ventilation rate from ACH to volumetric flow (m^3/h)
# ACH = flow (m^3/h) / volume (m^3)
# flow (m^3/h) = ACH * volume
flow_rate_m3_per_h = vent_rate * room_volume

# Initialize arrays to store results
time_array = np.arange(0, total_hours, dt)
concentration = np.zeros(num_steps)  # quanta/m^3 in the space

# Utility: find out who is present at a given time
def get_current_occupants(current_minute, arrivals):
    """
    Return a list of occupant_ids who are in the toilet 
    at the specified current_minute.
    """
    occupant_ids = []
    for person in arrivals:
        start = person['arrival_time']
        end = person['arrival_time'] + person['dwell_time']
        if start <= current_minute < end:
            occupant_ids.append(person['occupant_id'])
    return occupant_ids

# We’ll store who was present in each time step for dose calculation
occupants_over_time = [[] for _ in range(num_steps)]

# ---------------------------------------------------
# 4. RUN THE TIME-STEPPING SIMULATION
# ---------------------------------------------------

for t_idx, current_hour in enumerate(time_array):
    current_minute = current_hour * 60.0
    
    # 4.1 Identify who is present
    occupants_present = get_current_occupants(current_minute, arrivals)
    occupants_over_time[t_idx] = occupants_present
    
    # 4.2 Determine the number of infectious individuals present
    #     and calculate aerosol generation for this time step
    if t_idx == 0:
        # Starting concentration is zero or background
        concentration_prev = 0.0
    else:
        concentration_prev = concentration[t_idx - 1]
    
    # Infectious generation
    # Count how many infectious occupants are present
    num_infectious = 0
    for person in arrivals:
        start = person['arrival_time']
        end = person['arrival_time'] + person['dwell_time']
        if start <= current_minute < end and person['infectious']:
            num_infectious += 1
    
    # Quanta generation rate in quanta/hour
    total_gen_rate = num_infectious * quanta_generation_rate
    
    # 4.3 Update concentration using a simple well-mixed model:
    # dC/dt = (Total_generation_rate / Volume) - (Vent_out + Decay)*C
    # Solve in small discrete steps (Euler method)
    # 
    #   C(t+dt) = C(t) + dt * [ (G/V) - (k + Q/V)*C(t) ]
    # where:
    #   G = total_gen_rate [quanta/h]
    #   V = room_volume [m^3]
    #   Q = flow_rate_m3_per_h [m^3/h]
    #   k = decay_rate [h^-1]
    
    gen_term = total_gen_rate / room_volume
    removal_term = (decay_rate + flow_rate_m3_per_h/room_volume)
    
    C_new = concentration_prev + dt * (gen_term - removal_term * concentration_prev)
    concentration[t_idx] = max(C_new, 0.0)  # ensure no negative
    
    # 4.4 Update occupant doses
    # Each occupant present inhales some fraction of concentration:
    #   dose_inhaled = inhalation_rate * concentration * dt
    # 
    # For simplicity, let's assume a constant inhalation rate, e.g. 0.5 m^3/hour
    inhalation_rate = 0.5  # m^3 per hour
    # dose_inhaled (quanta) = C(t) (quanta/m^3) * InhRate (m^3/h) * dt (h)
    
    for occ_id in occupants_present:
        occupant_dose[occ_id] += concentration[t_idx] * inhalation_rate * dt

# ---------------------------------------------------
# 5. POST-PROCESSING & PLOTS
# ---------------------------------------------------

# Extract final occupant dose
# occupant_dose is a dictionary {occ_id: dose_quanta}
# You can convert it to a list to plot histograms or examine distribution
dose_values = list(occupant_dose.values())

# For demonstration, let's show:
# 1) Time series of concentration
# 2) Distribution of total dose among the visitors

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 1) Plot concentration
ax1.plot(time_array, concentration, label='Airborne Concentration')
ax1.set_xlabel('Time (hours)')
ax1.set_ylabel('Concentration (quanta/m³)')
ax1.set_title('Aerosol Concentration Over 24h')
ax1.legend()
ax1.grid(True)

# 2) Histogram of cumulative dose
ax2.hist(dose_values, bins=20, edgecolor='black')
ax2.set_xlabel('Inhaled Dose (quanta)')
ax2.set_ylabel('Number of People')
ax2.set_title('Distribution of Cumulative Dose')
ax2.grid(True)

plt.tight_layout()
plt.show()

# ---------------------------------------------------
# 6. EXAMPLE OF PER-PERSON EXPOSURE TRACKING
# ---------------------------------------------------
# occupant_dose dictionary holds the total dose each occupant received.
# If you want to see each occupant's data (e.g., arrival_time, dose, etc.):
for person in arrivals[:50]:  # just show the first 5 for brevity
    occ_id = person['occupant_id']
    print(f"OccID: {occ_id}, Arrival: {person['arrival_time']:.1f} min, "
          f"Dwell: {person['dwell_time']:.1f} min, "
          f"Infectious: {person['infectious']}, "
          f"Cumulative Dose: {occupant_dose[occ_id]:.3f} quanta")