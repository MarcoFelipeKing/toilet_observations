#Install and load packages 
install.packages("ggplot2") # for plotting
install.packages("readr")  # reads csv
install.packages("tidyr")#pivot longer
install.packages("reshape2") #for melting data frames 
library(ggplot2)
library(readr)
library(tidyr)
library(reshape2)

# Load the transition matrix data
transition_matrix <- read_csv("C:/Users/CNBH/Documents/GitHub/toilet_observations/contacts/outputs/transition_matrix.csv")

#print(head(transition_matrix)) #to see data

#set row names using the first column
rownames(transition_matrix) <- transition_matrix$`...1`

# Remove the first column which is now redundant as row names
#transition_matrix <- transition_matrix[, -1]

# Verify the row names and structure
#print(head(transition_matrix))
#print(rownames(transition_matrix))

# Melting the data frame. Assuming 'State' as the first column containing row identifiers.
data_long <- melt(transition_matrix[, -1], variable.name = "To_State", value.name = "Probability")

# Adding row names as a column for ggplot
data_long$From_State <- rownames(transition_matrix)

# Create the heatmap
heatmap_plot <- ggplot(data_long, aes(x = From_State, y = To_State, fill = Probability)) +
  geom_tile() +  # This creates the tiles for the heatmap
  scale_fill_gradient(low = "orange", high = "blue", na.value = "white", limits = c(0, 1)) +  # Adjust color gradient
  labs(title = "Transition Matrix Heatmap: Sequence of Surface Contacts During Urination in Men's Toilet (handwashing setting)",
       x = "From State",
       y = "To State",
       fill = "Probability") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1))  # Adjust text angle for better readability

print(heatmap_plot)

#ggsave(path = "C:/Users/CNBH/Documents/GitHub/toilet_observations/contacts/outputs/images",filename="heatmaps_fem_ss_urin_cubicle_10.png",width = 15,height=10,units = "in",bg = "white")
