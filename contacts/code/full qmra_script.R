
#STEP 1 = LOAD IN MY DATA AND RENAME SOME OF MY EVENTS
pacman::p_load(dplyr,vroom,tidyr,tidytext,ggplot2,stringr,stringi,ggpubr,RColorBrewer
,paletteer,plotly,kableExtra,ggpval,viridis,plotrix,rstatix,car,htmltools,pwr,pwr2,tibble,clickstream,devtools,TraMineR,markovchain)
require(dplyr)
require(markovchain)
require(vroom)
df<-vroom::vroom(file="../data/clean_contact_data.csv")

df <- df %>%
  mutate(Surface = str_trim(Surface)) %>%
  mutate(Surface = if_else(str_detect(Surface, "Outside door handle"), 
                           str_replace(Surface, "Outside door handle", "Door handle outside"), 
                           Surface)) %>% 
  mutate(Surface = if_else(str_detect(Surface, "Inside door handle"), 
                           str_replace(Surface, "Inside door handle", "Door handle inside"), 
                           Surface))


# Proportion of left and right hand contacts per surface
hands_proportions <- df %>% 
  filter(Hand!="N/A" & Hand!="Both", Toilet_type!="Gender neutral", Activity=="Urination") %>% 
  group_by(Toilet_type, Hand) %>% 
  tally() %>%
  mutate(proportion=prop.table(n))

# Save the table output to a CSV file
write.csv(hands_proportions, "hands_proportions_v2.csv", row.names = FALSE)


df$SurfaceCategories[df$Surface=="Cubicle door handle inside" |
                       df$Surface=="Cubicle door handle outside"]<-"Entry/Exit"

setwd("C:/Users/CNBH/Documents/GitHub/toilet_observations/contacts/code")

#STEP 2 = SET UP MY SEQUENCE GENERATOR FUNCTION
source("sequence_function.R")

#---------------------THIS WILL ALL BE REPEATED.... 

#STEP 3 = GENERATE MY SEQUENCES FOR THE EXPOSURE MODEL FOR CASE _________ 
generate_my_sequences(df, "Female", "Urination", "Women", num.people=10)

#STEP 4 = SETTING UP MY PARAMETERS FOR THE EXPOSURE MODEL

#STEP 5 = RUNNING THE EXPOSURE AND DOSE-RESPONSE MODEL

#STEP 6 = SAVING MY RISK OUTPUTS

#---------------------- X ALL OF MY CASES

#STEP 7 = SUMMARY STATISTICS AND PLOTS OF RESULTS

