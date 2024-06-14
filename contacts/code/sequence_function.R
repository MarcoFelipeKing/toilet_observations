# Define the create_markov_chain function
create_markov_chain <- function(df, Sex, Activity, Toilet_type, num.people, file_name) {
  
  # Create a list of all valid combinations
  valid_combinations <- df %>%
    distinct(Sex, Activity, Toilet_type)
  
  # Convert to a list of lists
  valid_combinations_list <- valid_combinations %>%
    rowwise() %>%
    mutate(combo = list(list(Sex = Sex, Activity = Activity, Toilet_type = Toilet_type))) %>%
    pull(combo)
  
  # Validate parameters .....(NOT RUNNING PROPERLY- SEX NOT FOUND)
  if (!any(sapply(valid_combinations_list, function(combo) {
    combo$Sex == Sex && combo$Activity == Activity && combo$Toilet_type == Toilet_type
  }))) {
    stop("Invalid combination of Sex, Activity, and Toilet_type")
  }
  
  # Filter the data based on sex, activity, toilet type & surface category
  filter_data <- function(df, Sex, Activity, Toilet_type, categories) {
    df %>%
      filter(Sex == !!Sex & Activity == !!Activity & Toilet_type == !!Toilet_type & SurfaceCategories %in% categories) %>% 
      arrange(ExperimentID)
  }
  if (Sex == "Male" & Activity == "Urination" & Toilet_type == "Men") {
    subset_data_cubicle <- filter_data(df, Sex, Activity, Toilet_type, c("Personal"))
    subset_data_hygiene <- filter_data(df, Sex, Activity, Toilet_type, c("Hygiene"))
    
  } else if (Sex == "Female" & Activity == "MHM" & (Toilet_type == "Women" | Toilet_type == "Gender neutral")) {
    subset_data_mhm <- filter_data(df, Sex, Activity, Toilet_type, c("Personal", "Cubicle", "MHM"))
    
  } else {
    subset_data_cubicle <- filter_data(df, Sex, Activity, Toilet_type, c("Personal", "Cubicle"))
    subset_data_hygiene <- filter_data(df, Sex, Activity, Toilet_type, c("Hygiene"))
  }
  
  # Print filtered data for debugging
  #print(paste("Filtered Data for", Sex, Activity, Toilet_type, "Cubicle/Personal:"))
  #print(subset_data_cubicle)
  #print(paste("Filtered Data for", Sex, Activity, Toilet_type, "Hygiene:"))
  #print(subset_data_hygiene)
  #print(paste("Filtered Data for", Sex, Activity, Toilet_type, "MHM:"))
  #print(subset_data_mhm)
  
  # Create a list of sequences for each experiment
  create_sequence_list <- function(subset_data) {
    experiment_ids <- unique(subset_data$ExperimentID)
    lapply(experiment_ids, function(id) subset_data$Surface[subset_data$ExperimentID == id])
  }
  list.personal.cubicle <- create_sequence_list(subset_data_cubicle)
  list.hygiene <- create_sequence_list(subset_data_hygiene)
  list.mhm <- create_sequence_list(subset_data_mhm)
  
  
  # Fit Markov chains
  mc_personal_cubicle <- markovchainFit(data = list.personal.cubicle)$estimate
  mc_hygiene <- markovchainFit(data = list.hygiene)$estimate
  mc_mhm <- markovchainFit(data = list.mhm)$estimate
  
  # Access the transition matrix and save to object 
  transition_matrix_personal_cubicle <- mc_personal_cubicle@transitionMatrix
  transition_matrix_hygiene <- mc_hygiene@transitionMatrix
  transition_matrix_mhm <- mc_mhm@transitionMatrix
  print(transition_matrix_personal_cubicle)
  print(transition_matrix_hygiene)
  print(transition_matrix_mhm)
  write.csv(transition_matrix_personal_cubicle, file = paste0(file_name, "_personal_cubicle.csv"), row.names = TRUE)
  write.csv(transition_matrix_hygiene, file = paste0(file_name, "_hygiene.csv"), row.names = TRUE)
  write.csv(transition_matrix_mhm, file = paste0(file_name, "_mhm.csv"), row.names = TRUE)
  
  # Generate sequences for all people
  all.my.events <- vector("list", num.people)
  generate_events <- function(states, transition_matrix, initial_event, stop_events) {
    events <- initial_event
    i <- length(events) + 1
    while (!events[i-1] %in% stop_events) {
      next_event <- if (i == length(events) + 1) {
        sample(states, 1)
      } else {
        sample(states, 1, replace = TRUE, prob = transition_matrix[events[i-1], ])
      }
      events <- c(events, next_event)
      i <- i + 1
    }
    #events
  }
  for (p in 1:num.people) {
    if (Sex == "Male" & Activity == "Urination") {
      events <- c("Door handle outside")
      events <- generate_events(rownames(transition_matrix_personal_cubicle), transition_matrix_personal_cubicle, events, c("Flush button", "Toilet surface"))
      i.final <- length(events)
    } else if (Sex == "Female" & Activity == "MHM") {
      events <- c("Door handle outside", "Cubicle door handle outside")
      events <- generate_events(rownames(transition_matrix_mhm), transition_matrix_mhm, events, c("Flush button", "Toilet surface"))
      events <- c(events, "Cubicle door handle inside")
      i.final <- length(events)
    } else {
      events <- c("Door handle outside", "Cubicle door handle outside")
      events <- generate_events(rownames(transition_matrix_personal_cubicle), transition_matrix_personal_cubicle, events, c("Flush button", "Toilet surface"))
      events <- c(events, "Cubicle door handle inside")
      i.final <- length(events)
    }
    events <- generate_events(rownames(transition_matrix_hygiene), transition_matrix_hygiene, events, c("Bin outside the cubicle", "Hand dryer"))
    events <- c(events, "Door handle inside")
    all.my.events[[p]] <- events
  }
  # Return the event sequences
  return(all.my.events)
  
} #end of my function bracket

# Assuming all.my.events is your list of sequences
# Convert list of sequences to a data frame
events_df <- do.call(rbind, lapply(all.my.events, function(x) {
  tibble(Event = x)
}))

# Save the sequence data frame to a CSV file
write.csv(events_df, "C:/Users/CNBH/Documents/GitHub/toilet_observations/contacts/outputs/all_events_sequences.csv", row.names = FALSE)

# Initialize matrix with zeros for all possible states
states <- unique(unlist(all.my.events))  # Get all unique states
transition_matrix <- matrix(0, nrow = length(states), ncol = length(states), dimnames = list(states, states))

# Fill the transition matrix with counts
for (sequence in all.my.events) {
  for (i in seq_len(length(sequence) - 1)) {
    transition_matrix[sequence[i], sequence[i + 1]] <- transition_matrix[sequence[i], sequence[i + 1]] + 1
  }
}

# Convert counts to probabilities (optional)
transition_matrix <- sweep(transition_matrix, 1, rowSums(transition_matrix), `/`)

# Save the transition matrix to a CSV file
write.csv(transition_matrix, "C:/Users/CNBH/Documents/GitHub/toilet_observations/contacts/outputs/transition_matrix.csv", row.names = TRUE)

# Print out a sample of what has been saved to ensure correctness
print(head(events_df))
print(transition_matrix)

# NOTES-------------------------------------------------------------------------------------------------------

# event.length<-rep(NA,num.people)
# for(k in 1:num.people){
#  event.length[k]<-length(all.my.events[[k]])
#} 

#summary(event.length)
#view(all.my.events[500])


# View the estimated transition matrix

# Toilet_type <- unique(df$Toilet_type) 

#  print(paste("Transition Matrix for", "Sex", ":", "Activity", "-", "SurfaceCategories", "-", Toilet_type))

# print(mc$estimate)

# Return the Markov chain object
#  return(mc)

