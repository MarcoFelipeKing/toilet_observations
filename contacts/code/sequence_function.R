# Define the create_markov_chain function

create_markov_chain <- function(df, Sex, Activity, Toilet_type, num.people,file_name) {
  
  
  # Filter the data based on sex, activity, toilet type & surface category
  
  if (Sex=="Male" & Activity=="Urination" & Toilet_type=="Men"){
    
    subset_data_cubicle <- df %>%
      filter(Sex==Sex & Activity == Activity & SurfaceCategories == c("Personal"))%>%
      arrange(ExperimentID)
    
    subset_data_hygiene <- df %>%
      filter(Sex==Sex & Activity == Activity & SurfaceCategories == c("Hygiene"))%>%
      arrange(ExperimentID)
    
  }else{
    subset_data_cubicle <- df %>%
      filter(Sex==Sex & Activity == Activity & SurfaceCategories == c("Personal","Cubicle"))%>%
      arrange(ExperimentID)
    
    subset_data_hygiene <- df %>%
      filter(Sex==Sex & Activity == Activity & SurfaceCategories == c("Hygiene"))%>%
      arrange(ExperimentID)
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
  
  
  mc_personal_cubicle <- markovchainFit(data = list.personal.cubicle)

  mc_hygiene <- markovchainFit(data = list.hygiene)
  

  # Access the transition matrix and save to object 
  #Save each transition matrix with a unique name based on the subset
  transition_matrix_personal_cubicle <- mc_personal_cubicle$estimate@transitionMatrix
  states <- rownames(transition_matrix_personal_cubicle) # This line might not be needed unless used later
  print(transition_matrix_personal_cubicle)
  write.csv(transition_matrix_personal_cubicle, file = paste0(file_name, "_personal_cubicle.csv"), row.names = TRUE)
  
  transition_matrix_hygiene<-mc_hygiene$estimate@transitionMatrix
  states_hygiene<- rownames(transition_matrix_hygiene) # This line might not be needed unless used later
  write.csv(transition_matrix_hygiene, file = paste0(file_name, "_hygiene.csv"), row.names = TRUE)
  
  #Generate sequences for all my people
  all.my.events<<-list()
  
  
  for (p in 1:num.people){
    #print(p)
    
    # Predict the next surface contact
    if(Sex=="Male" & Activity=="Urination"){
      events<-c("Door handle outside")
      i<-2
    }else{
      events<-c("Door handle outside", "Cubicle door handle outside")
      i<-3
    }
    
    while(events[i-1]!="Flush button" & events[i-1]!="Toilet surface"){
      if (Sex=="Male" & Activity=="Urination"){
        if (i==2){
          nextevent<-sample(states,1)
        }else{
          nextevent<-sample(states,1,replace=TRUE,prob=transition_matrix_personal_cubicle[events[i-1],])
        }
      }else{
        if (i==3){
          nextevent<-sample(states,1)
        }else{
          nextevent<-sample(states,1,replace=TRUE,prob=transition_matrix_personal_cubicle[events[i-1],])
        }
      }
     
      events<-c(events,nextevent)
      i<-i+1
    }
    
    if (Sex=="Male" & Activity=="Urination"){
      i=i.final
    }else{
      events<-c(events,"Cubicle door handle inside")
      i.final<-i+1
      i=i.final
    }
   
    while(events[i-1]!="Bin outside the cubicle" & events[i-1]!="Hand dryer"){
      if (i==i.final){
        nextevent<-sample(states_hygiene,1)
      }else{
        nextevent<-sample(states_hygiene,1,replace=TRUE,prob=transition_matrix_hygiene[events[i-1],])
      }
      events<-c(events,nextevent)
      i<-i+1
    }
    
    events<-c(events,"Door handle inside")
    
    all.my.events[[p]]<<-events
  } #end of my loop for making sequences for all num.people
  
  #saving all of my event sequences globally (i.e., I can access it outside the function!)
  #all.my.events<<-all.my.events
  return(all.my.events)
} #end of my function bracket



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

