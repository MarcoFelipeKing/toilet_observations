library(dplyr)
library(markovchain)

# Define the create_markov_chain function
create_markov_chain <- function(df, Sex, Activity, Toilet_type, num.people, file_name) {
  
  # Create a list of all valid combinations
  
  if (!"Sex" %in% colnames(df)) {
    stop("Sex column not found in the dataframe")
  } else {
    valid_combinations <- df %>%
      distinct(Activity, Toilet_type, Sex)
  }
  
  # Convert to a list of lists
  valid_combinations_list <- valid_combinations %>%
    rowwise() %>%
    mutate(combo = list(list(Sex = Sex, Activity = Activity, Toilet_type = Toilet_type))) %>%
    pull(combo)
  
  # Using `with()` to ensure the variables are accessible within the scope of the sapply function
  if (!any(with(list(Sex = Sex, Activity = Activity, Toilet_type = Toilet_type), 
                sapply(valid_combinations_list, function(combo) {
                  combo$Sex == Sex && combo$Activity == Activity && combo$Toilet_type == Toilet_type
                })))) {
    stop("Invalid combination of Sex, Activity, and Toilet_type")
  }
  
  
  # Filter the data based on sex, activity, toilet type & surface category
  
  create_subset_data <- function(df) {
    # Make sure df has the columns we expect
    if(!all(c("Sex", "Activity", "Toilet_type") %in% names(df))) {
      stop("DataFrame missing required columns")
    }
    
    # Iterate over each row of the DataFrame
    apply(df, 1, function(row) {
      Sex <- row["Sex"]
      Activity <- row["Activity"]
      Toilet_type <- row["Toilet_type"]
      
      if (Sex == "Male" & Activity == "Urination" & Toilet_type == "Men") {
        subset_data_cubicle <- filter_data(df, Sex, Activity, Toilet_type, c("Personal", "Entry"))
        subset_data_hygiene <- filter_data(df, Sex, Activity, Toilet_type, c("Hygiene", "Personal", "Exit"))
        
      } else if (Sex == "Female" & Activity == "MHM" & Toilet_type %in% c("Women", "Gender neutral")) {
        subset_data_cubicle <- filter_data(df, Sex, Activity, Toilet_type, c("Personal", "Cubicle", "MHM", "Entry", "CubicleIn", "CubicleOUT"))
        subset_data_hygiene <- filter_data(df, Sex, Activity, Toilet_type, c("Hygiene", "Personal", "Exit"))
        
        
      } else if (Sex == "Female", "Male" & Activity == "Defecation" & Toilet_type %in% c("Women", "Gender neutral", "Men")) {
        subset_data_cubicle <- filter_data(df, Sex, Activity, Toilet_type, c("Personal", "Cubicle", "Entry", "CubicleIn", "CubicleOUT"))
        subset_data_hygiene <- filter_data(df, Sex, Activity, Toilet_type, c("Hygiene", "Personal", "Exit"))
        
      } else {
        subset_data_cubicle <- filter_data(df, Sex, Activity, Toilet_type, c("Personal", "Cubicle", "Entry", "CubicleIn", "CubicleOUT"))
        subset_data_hygiene <- filter_data(df, Sex, Activity, Toilet_type, c("Hygiene", "Personal", "Exit"))
      }
      
      # You might need to decide what to return or do with subset_data_cubicle and subset_data_hygiene
      # For now, just printing for demonstration
      print(subset_data_cubicle)
     print(subset_data_hygiene)
    })
  }
  
  # Example of calling the function
  #create_subset_data(df)
  
  
  # Print filtered data for debugging
 print(paste("Filtered Data for", Sex, Activity, Toilet_type, "Cubicle/Personal:"))
  print(subset_data_cubicle)
  print(paste("Filtered Data for", Sex, Activity, Toilet_type, "Hygiene/Personal:"))
  print(subset_data_hygiene)
  
  # Create a list of sequences for each experiment
  create_sequence_list <- function(subset_data) {
    experiment_ids <- unique(subset_data$ExperimentID)
    lapply(experiment_ids, function(id) subset_data$Surface[subset_data$ExperimentID == id])
  }
  
  # Create a Markov chain object
  list.personal.cubicle<-list()
  experiment.id.names<-unique(subset_data_cubicle$ExperimentID)
  for (i in 1: length(experiment.id.names)){
    list.personal.cubicle[[i]]<-subset_data_cubicle$Surface[subset_data_cubicle$ExperimentID==experiment.id.names[i]] 
  }
  
  list.hygiene<-list()
  experiment.hygiene.id.names<-unique(subset_data_hygiene$ExperimentID)
  for (i in 1: length(subset_data_hygiene$ExperimentID)){
    list.hygiene[[i]]<-subset_data_hygiene$Surface[subset_data_hygiene$ExperimentID==experiment.hygiene.id.names[i]] 
  }
  
  # Fit Markov chains
  mc_personal_cubicle <- markovchainFit(data = list.personal.cubicle)$estimate
  mc_hygiene <- markovchainFit(data = list.hygiene)$estimate
  
  # Access the transition matrix and save to object 
  transition_matrix_personal_cubicle <- mc_personal_cubicle@transitionMatrix
  transition_matrix_hygiene <- mc_hygiene@transitionMatrix
  print(transition_matrix_personal_cubicle)
  print(transition_matrix_hygiene)
  write.csv(transition_matrix_personal_cubicle, file = paste0(file_name, "_cubicle.csv"), row.names = TRUE)
  write.csv(transition_matrix_hygiene, file = paste0(file_name, "_hygiene.csv"), row.names = TRUE)
  
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
    events
  }
  for (p in 1:num.people) {
    if (Sex == "Male" & Activity == "Urination") {
      events <- c("Door handle outside")
      events <- generate_events(rownames(transition_matrix_personal_cubicle), transition_matrix_personal_cubicle, events, c("Flush button", "Toilet surface"))
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
}

