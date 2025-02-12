import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------------------------
# 1. MODEL SETUP
# --------------------------------------------------------------------

# Simulation duration & time step
TOTAL_HOURS = 8      # Example: 8-hour period
DT_MINUTES = 1
DT_HOURS = DT_MINUTES / 60
num_steps = int(TOTAL_HOURS / DT_HOURS)

time_array = np.arange(0, TOTAL_HOURS, DT_HOURS)

# --- ZONE PARAMETERS ---
# Let's define 3 zones: A (general area), B (cubicle 1), C (cubicle 2)

# Volumes (m^3)
V_A = 40.0  # general area
V_B = 5.0   # cubicle 1
V_C = 5.0   # cubicle 2

# Ventilation to outside (m^3/h)
Q_A_vent = 100.0  # example
Q_B_vent = 20.0
Q_C_vent = 20.0

# Inactivation/decay rates (h^-1)
k_A = 0.3
k_B = 0.3
k_C = 0.3

# Inter-zonal flow rates (m^3/h)
# We define Q_AtoB as the flow from A->B, Q_BtoA from B->A, etc.
# For simplicity, assume symmetrical flows:
Q_AtoB = 10.0
Q_BtoA = 10.0
Q_AtoC = 10.0
Q_CtoA = 10.0
# Assume no direct exchange between B and C (or set it if desired):
Q_BtoC = 0.0
Q_CtoB = 0.0

# Infectious aerosol generation
quanta_generation_rate = 10.0  # quanta/h per infectious occupant

# Occupant inhalation rate
INHALATION_RATE = 0.5  # m^3/hour

# Probability an occupant is infectious
prevalence = 0.05

# Random seed for reproducibility
np.random.seed(42)

# --------------------------------------------------------------------
# 2. ARRIVALS & OCCUPANT MOVEMENT
# --------------------------------------------------------------------

"""
We will create a simple occupant schedule:
  - A certain number of arrivals in 8 hours (Poisson)
  - Each occupant:
      1) Arrives at Zone A at some time
      2) Spends T_A minutes in the general area
      3) Chooses either Cubicle 1 or Cubicle 2
      4) Spends T_B or T_C minutes in that cubicle
      5) Leaves the system
"""

mean_arrivals_per_hour = 5
lambda_total = mean_arrivals_per_hour * TOTAL_HOURS
num_occupants = np.random.poisson(lambda_total)

# We'll store occupant info in a list of dicts
# occupant['occupant_id']
# occupant['arrival_time'] (minutes)
# occupant['zone_A_duration'] (minutes)
# occupant['cubicle'] (B or C)
# occupant['cubicle_duration'] (minutes)
# occupant['infectious'] (bool)
# occupant['dose'] (accumulated quanta)

occupants = []
for i in range(num_occupants):
    arrival_time = np.random.uniform(0, TOTAL_HOURS * 60)  # in minutes
    zone_A_duration = np.random.exponential(2.0)  # average 2 min in general area
    # randomly pick a cubicle
    if np.random.rand() < 0.5:
        cubicle = 'B'
    else:
        cubicle = 'C'
    cubicle_duration = np.random.exponential(3.0)  # average 3 min in cubicle
    
    is_infectious = (np.random.rand() < prevalence)
    
    occupants.append({
        'occupant_id': i,
        'arrival_time': arrival_time,
        'zone_A_duration': zone_A_duration,
        'cubicle': cubicle,
        'cubicle_duration': cubicle_duration,
        'infectious': is_infectious,
        'dose': 0.0
    })

# Sort by arrival_time
occupants = sorted(occupants, key=lambda x: x['arrival_time'])

def get_occupant_zone(occ, current_minute):
    """
    Given occupant dict and current time (minutes),
    return which zone the occupant is in: 'A', 'B', 'C', or None (left).
    """
    start = occ['arrival_time']
    A_end = start + occ['zone_A_duration']       # time occupant leaves zone A
    if occ['cubicle'] == 'B':
        B_start = A_end
        B_end = B_start + occ['cubicle_duration']
        # C never used for them
        if current_minute < start:
            return None  # not arrived
        elif start <= current_minute < A_end:
            return 'A'
        elif A_end <= current_minute < B_end:
            return 'B'
        else:
            return None  # left
    else:  # occupant['cubicle'] == 'C'
        C_start = A_end
        C_end = C_start + occ['cubicle_duration']
        if current_minute < start:
            return None
        elif start <= current_minute < A_end:
            return 'A'
        elif A_end <= current_minute < C_end:
            return 'C'
        else:
            return None

# --------------------------------------------------------------------
# 3. STATE VARIABLES & RESULTS STORAGE
# --------------------------------------------------------------------

# Concentrations in each zone over time
C_A = np.zeros(num_steps)
C_B = np.zeros(num_steps)
C_C = np.zeros(num_steps)

# --------------------------------------------------------------------
# 4. TIME-STEPPING SIMULATION (EULER)
# --------------------------------------------------------------------
for t_idx, t_hour in enumerate(time_array):
    current_minute = t_hour * 60
    
    # Previous step concentrations
    if t_idx == 0:
        cA_prev, cB_prev, cC_prev = 0.0, 0.0, 0.0
    else:
        cA_prev = C_A[t_idx - 1]
        cB_prev = C_B[t_idx - 1]
        cC_prev = C_C[t_idx - 1]
    
    # 4.1: Determine how many infectious occupants are in each zone
    inf_in_A = 0
    inf_in_B = 0
    inf_in_C = 0
    
    # Also track occupant presence for dose
    occupants_in_A = []
    occupants_in_B = []
    occupants_in_C = []
    
    for occ in occupants:
        zone = get_occupant_zone(occ, current_minute)
        if zone == 'A':
            occupants_in_A.append(occ)
            if occ['infectious']:
                inf_in_A += 1
        elif zone == 'B':
            occupants_in_B.append(occ)
            if occ['infectious']:
                inf_in_B += 1
        elif zone == 'C':
            occupants_in_C.append(occ)
            if occ['infectious']:
                inf_in_C += 1
    
    # 4.2: Quanta generation in each zone
    G_A = inf_in_A * quanta_generation_rate  # quanta/hour
    G_B = inf_in_B * quanta_generation_rate
    G_C = inf_in_C * quanta_generation_rate
    
    # 4.3: Compute new concentrations (Euler step)
    # For each zone i, the net flow in from j is Q_jtoI*C_j
    # outflow from i is Q_ItoJ*C_i plus Q_I_vent*C_i
    #
    # A-zone balance:
    # dC_A/dt = (1/V_A)* [ G_A
    #                     + Q_BtoA*cB_prev + Q_CtoA*cC_prev
    #                     - Q_AtoB*cA_prev - Q_AtoC*cA_prev - Q_A_vent*cA_prev ]
    #           - k_A*cA_prev
    
    flow_in_A = Q_BtoA*cB_prev + Q_CtoA*cC_prev
    flow_out_A = Q_AtoB*cA_prev + Q_AtoC*cA_prev + Q_A_vent*cA_prev
    dC_A_dt = (1.0 / V_A) * ( G_A + flow_in_A - flow_out_A ) - k_A*cA_prev
    cA_new = cA_prev + DT_HOURS * dC_A_dt
    
    # B-zone balance:
    # dC_B/dt = (1/V_B)* [ G_B
    #                     + Q_AtoB*cA_prev
    #                     - Q_BtoA*cB_prev - Q_B_vent*cB_prev ]
    #           - k_B*cB_prev
    
    flow_in_B = Q_AtoB*cA_prev
    flow_out_B = Q_BtoA*cB_prev + Q_B_vent*cB_prev
    dC_B_dt = (1.0 / V_B) * ( G_B + flow_in_B - flow_out_B ) - k_B*cB_prev
    cB_new = cB_prev + DT_HOURS * dC_B_dt
    
    # C-zone balance:
    # dC_C/dt = (1/V_C)* [ G_C
    #                     + Q_AtoC*cA_prev
    #                     - Q_CtoA*cC_prev - Q_C_vent*cC_prev ]
    #           - k_C*cC_prev
    
    flow_in_C = Q_AtoC*cA_prev
    flow_out_C = Q_CtoA*cC_prev + Q_C_vent*cC_prev
    dC_C_dt = (1.0 / V_C) * ( G_C + flow_in_C - flow_out_C ) - k_C*cC_prev
    cC_new = cC_prev + DT_HOURS * dC_C_dt
    
    # Store updated concentrations
    C_A[t_idx] = max(cA_new, 0.0)
    C_B[t_idx] = max(cB_new, 0.0)
    C_C[t_idx] = max(cC_new, 0.0)
    
    # 4.4: Update occupant doses
    # occupant_dose += concentration_in_zone * inhalation_rate * dt
    for occ in occupants_in_A:
        occ['dose'] += C_A[t_idx] * INHALATION_RATE * DT_HOURS
    for occ in occupants_in_B:
        occ['dose'] += C_B[t_idx] * INHALATION_RATE * DT_HOURS
    for occ in occupants_in_C:
        occ['dose'] += C_C[t_idx] * INHALATION_RATE * DT_HOURS

# --------------------------------------------------------------------
# 5. POST-PROCESSING & VISUALIZATION
# --------------------------------------------------------------------

# Summarize occupant dose distribution
all_doses = [occ['dose'] for occ in occupants]

# Plot concentration in each zone over time
plt.figure(figsize=(10,5))
plt.plot(time_array, C_A, label='Zone A (General Area)')
plt.plot(time_array, C_B, label='Zone B (Cubicle 1)')
plt.plot(time_array, C_C, label='Zone C (Cubicle 2)')
plt.xlabel('Time (hours)')
plt.ylabel('Concentration (quanta/m³)')
plt.title('Multi-Zone Airborne Concentration')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot occupant dose histogram
plt.figure(figsize=(6,4))
plt.hist(all_doses, bins=20, edgecolor='black')
plt.xlabel('Inhaled Dose (quanta)')
plt.ylabel('Number of Occupants')
plt.title('Distribution of Cumulative Inhaled Dose')
plt.grid(True)
plt.tight_layout()
plt.show()

# Print a few occupants for inspection
print("Sample occupant data:")
for occ in occupants[:10]:
    print(f"ID={occ['occupant_id']}, "
          f"Arrival={occ['arrival_time']:.1f} min, "
          f"ZoneA_dur={occ['zone_A_duration']:.1f} min, "
          f"Cubicle={occ['cubicle']}, "
          f"Cubicle_dur={occ['cubicle_duration']:.1f} min, "
          f"Infectious={occ['infectious']}, "
          f"Dose={occ['dose']:.4f} quanta")