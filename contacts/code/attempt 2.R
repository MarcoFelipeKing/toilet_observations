

# Load files --------------------------------------------------------------
{r setup, include=FALSE, warning=FALSE, message=FALSE}
knitr::opts_chunk$set(echo = TRUE)
pacman::p_load(dplyr,vroom,tidyr,tidytext,ggplot2,stringr,stringi,ggpubr,RColorBrewer,paletteer,plotly,kableExtra,ggpval,viridis,plotrix,rstatix,car,htmltools,pwr,pwr2,tibble,clickstream,devtools,TraMineR,markovchain)

setwd("C:/Users/CNBH/Documents/GitHub/toilet_observations/contacts")

# Check the new working directory
getwd()

df<-vroom(file="toilet_observations/contacts/data/clean_contact_data.csv") 
janitor::clean_names()

df
```

