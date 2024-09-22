#1. Install and load libraries 

install.packages("truncdist")  # For truncated distributions
install.packages("dplyr")      # For data manipulation
install.packages("ggplot2")    # For plotting
install.packages("drc")
library(truncdist)
library(dplyr)
library(ggplot2)
library(drc)

# 2. DEFINE PARAMETERS
num_people <- 10000  # Number of simulations
activity <- "Urination"  
toilet_type <- "Men"  
sex <- "Male"  

# Surface contact frequencies (Average number of contacts)
average_contacts <- 10  

#3. SIMULATE TRANSFER EFFICIENCIES

TE_SH <- rtrunc(num_people, spec="norm", a=0, b=1, mean=0.23, sd=0.19) #TE surface to hand (metal, Anderson & Boehm, 2021)
TE_HS <- rtrunc(num_people, spec="norm", a=0, b=1, mean=0.18, sd=0.20) #TE hand to surface (metal, Anderson & Boehm, 2021)
TE_HM <- rep(0.34, num_people) #TE hand to mouth 

#4. SIMULATE SURFACE AREAS AND SURFACE CONCENTRATIONS

A_hand<- 910 #cm^2: Julian et al., 2018
A_surface_min <- 13
A_surface_max <- 641
C_surf_min <- 28.1 
C_surf_max <- 132.7
A_mouth <- 41 # surface area of mouth- max area used from AuYeung 2008
HM_area <- 2 #surface area of hand in contact with mouth (Amoah et al)
C_hand <- c() 


C_surf <- runif(num_people, min=C_surf_min, max=C_surf_max)
A_surfaces <- runif(num_people, min=A_surface_min, max=A_surface_max)

FSA <- 0.25 * A_hand/A_surfaces  # FSA max of 0.25 from AuYeung 2008: 25% of 910cm^2

#5. SIMULATE VIRAL LOAD ON HANDS AFTER CONTACT

simulate_viral_load <- function(C_hand_initial, TE_SH, FSA, C_surf, TE_HS) {
  # Calculate the new viral load on hands based on the provided equation
  C_hand_new <- C_hand_initial + (TE_SH * FSA * C_surf) - (TE_HS * FSA * C_hand_initial)
  return(C_hand_new)
}
# 6. CALCULATE THE NEW CONCENTRATION ON SURFACES (C_surf_new)
simulate_surface_concentration <- function(TE_SH, A_hand, A_surfaces, C_surf, TE_HS, FSA, C_hand) {
  C_surf_new <- TE_SH * (A_hand / A_surfaces) * C_surf + TE_HS * FSA * (A_hand / A_surfaces) * C_hand
  return(C_surf_new)
}
# Initialize initial concentration on hands (assuming it's 0 at the start)
C_hand_initial <- rep(0, num_people)  # Initially, no virus on hands

#Creating loop to run exposure model 
for(i in 1: (average_contacts)){
  # Apply the function to simulate the viral load
  if (i==1) {
    C_hand <- simulate_viral_load(C_hand_initial, TE_SH, FSA, C_surf, TE_HS)} 
    else {
      C_hand <- simulate_viral_load(C_hand, TE_SH, FSA, C_surf, TE_HS) 
    }
  
  # Simulate the new concentration on surfaces after hand contact
  C_surf_new <- simulate_surface_concentration(TE_SH, A_hand, A_surfaces, C_surf, TE_HS, FSA, C_hand)
  
}

# 7. CALCULATE CONCENTRATION ON HAND AFTER HAND-TO-MOUTH CONTACT
simulate_hand_after_hm_contact <- function(C_hand, TE_HM) {
  # Calculate new concentration on hand after hand-to-mouth contact using the correct equation
  C_hand_after_hm <- C_hand - TE_HM * C_hand
  return(C_hand_after_hm)
}

# Simulate the concentration on hands after hand-to-mouth contact
C_hand_after_hm <- simulate_hand_after_hm_contact(C_hand, TE_HM)

# Optional: print the concentration on hand after hand-to-mouth contact for debugging
print(C_hand_after_hm)

#8. CALCULATE DOSE AFTER HAND-TO-MOUTH CONTACT
Dose <- TE_HM * HM_area * C_hand
print(Dose)

#9.INCORPORATE HAND WASHING EVENTS 

# Handwashing Reduction (log10)
handwash_mean <- 1.62
handwash_sd <- 0.12

# Simulate log10 handwashing reduction
handwash_reduction <- rnorm(num_people, mean=handwash_mean, sd=handwash_sd)

# Convert log10 reduction to a multiplicative factor
handwash_factor <- 10^(-handwash_reduction)

# Apply handwashing to the viral load on hands
C_hand_after_wash <- C_hand * handwash_factor

# Recalculate Dose after handwashing
Dose_after_wash <- TE_HM * A_hand * C_hand_after_wash

# 10. DEFINE EXPONENTIAL DOSE-RESPONSE FUNCTION

# Exponential model parameter for SARS-CoV-2
k <- 4.1e2 #infectivity constanct for SARS-CoV(Amoah et al., 2021) )

# Define the exponential dose-response function
exponential_risk <- function(dose, k) {
  risk <- 1 - exp(- dose/k)
  return(risk)
}

# 11. CALCULATE INFECTION RISK USING EXPONENTIAL MODEL

# Calculate infection risk before and after handwashing using the exponential model

infection_risk_before <- 1 - exp(-Dose/k)
infection_risk_after <- 1 - exp(-Dose_after_wash/k)

# 12. RUN THE MODEL ACROSS ALL SIMULATIONS
results <- data.frame(
  TE_SH = TE_SH,
  TE_HS = TE_HS,
  TE_HM = TE_HM,
  A_hand = A_hand,
  A_surfaces = A_surfaces,  # Surface area of objects
  C_surf = C_surf,
  C_surf_new = C_surf_new,  # Surface concentration after hand contact
  C_hand = C_hand,
  C_hand_after_hm = C_hand_after_hm,  # Hand concentration after hand-to-mouth contact
  C_hand_after_wash = C_hand_after_wash,
  Dose = Dose,
  Dose_after_wash = Dose_after_wash,
  FSA = FSA,  # Fractional Surface Area
  A_mouth = A_mouth,  # Surface area of the mouth
  HM_area = HM_area,  # Hand-to-mouth contact area
  infection_risk_before = infection_risk_before,
  infection_risk_after = infection_risk_after
)


# 13. SAVE THE DATA TO CSV FILE

file_name <- paste0("results_with_exponential_risk_", activity, "_", toilet_type, "_", num_people, "_people.csv")
write.csv(results, file = file_name, row.names = FALSE)

#Plot simple dose-response curve 
plot(log10(1:10000), 1-exp(-(1:10000)/410))

# Plot dose-response curve with custom axis labels

# Load ggplot2 library
library(ggplot2)

# Create a data frame for Dose and Probability of Response
dose_data <- data.frame(
  Dose = log10(1:10000),
  Probability = 1 - exp(-(1:10000) / 410)
)

# Plot dose-response curve using ggplot2
ggplot(dose_data, aes(x = Dose, y = Probability)) +
  geom_line(color = "black", size = 1.2) +  # Line plot with custom color and size
  labs(title = "Dose-Response Curve", x = "Dose (log10(1:10000))", y = "Probability of Response") +  # Labels for title and axes
  theme_minimal()  # Use a minimal theme for a cleaner look

# Optional: Save the plot to a file
ggsave("dose_response_curve_ggplot.png")

#--------------------

# two dose response curves in the same graph

# Load ggplot2 library
library(ggplot2)

# Create two data frames for two different dose-response curves
dose_data <- data.frame(
  Dose = log10(1:10000),
  Probability1 = 1 - exp(-(1:10000) / 410),   # First curve
  Probability2 = 1 - exp(-(1:10000) / 200)    # Second curve with a different k value
)

# Convert to long format for ggplot compatibility
dose_data_long <- tidyr::pivot_longer(dose_data, cols = starts_with("Probability"), 
                                      names_to = "Curve", values_to = "Probability")

# Plot both dose-response curves using ggplot2
ggplot(dose_data_long, aes(x = Dose, y = Probability, color = Curve)) +
  geom_line(size = 1.2) +  # Line plot with custom line width
  labs(title = "Dose-Response Curves", x = "Dose", y = "Probability of Response") +  # Labels for title and axes
  theme_minimal() +  # Use a minimal theme for cleaner aesthetics
  scale_color_manual(values = c("blue", "red"), labels = c("Curve 1", "Curve 2"))  # Custom colors and labels

# Optional: Save the plot to a file
ggsave("two_dose_response_curves.png")


# 14. FIT AN EXPONENTIAL DOSE-RESPONSE MODEL AND GENERATE PLOT

# Fit an exponential dose-response model
#exponential_model <- drm(infection_risk_before ~ Dose, data=results, fct = EXD.2())

# Generate the plot with confidence intervals
#plot(exponential_model, type="confidence", main="Exponential Model with Confidence Bounds",
 #    xlab="Dose", ylab="Probability of Response",
  #   ylim=c(0, 1))

# Add 95% and 99% confidence intervals
#plot(exponential_model, add=TRUE, type="confidence", level=0.95, lty=2)
#plot(exponential_model, add=TRUE, type="confidence", level=0.99, lty=3)

# Save the plot
#ggsave("exponential_model_confidence_plot.png")


# 15. SENSITIVITY ANALYSIS

# Adjust a parameter and re-run
TE_SH_mean_new <- 0.25
TE_SH_new <- rtrunc(num_people, spec="norm", a=0, b=1, mean=TE_SH_mean_new, sd=TE_SH_sd)
# Recalculate viral load and dose with the new TE_SH
C_hand_new <- simulate_viral_load(TE_SH_new, A_hand, C_surf)
Dose_new <- TE_HM * A_hand * C_hand_new
infection_risk_new <- exponential_risk(Dose_new, k)

# Add these new results to a new results data frame for comparison if necessary

#---------------------------

#ANALYSE AND PLOT RESULTS 

ggplot(results, aes(x=C_hand_after_wash, y=Dose_after_wash)) +
  geom_point() +
  labs(title="Viral Load on Hands vs. Dose",
       x="Viral Load on Hands",
       y="Dose")

# Plot infection risk before and after handwashing
ggplot(results, aes(x=infection_risk_before)) +
  geom_histogram(bins=30, fill="red", alpha=0.7) +
  labs(title="Histogram of Infection Risk Before Handwashing",
       x="Infection Risk (Before Handwashing)",
       y="Frequency") +
  theme_minimal()

ggplot(results, aes(x=infection_risk_after)) +
  geom_histogram(bins=30, fill="green", alpha=0.7) +
  labs(title="Histogram of Infection Risk After Handwashing",
       x="Infection Risk (After Handwashing)",
       y="Frequency") +
  theme_minimal()

# SUMMARY STATISTICS FOR DOSE

# Calculate summary statistics for Dose
mean_dose <- mean(Dose)
median_dose <- median(Dose)
sd_dose <- sd(Dose)
range_dose <- range(Dose)

# Calculate summary statistics for Dose_after_wash
mean_dose_after_wash <- mean(Dose_after_wash)
median_dose_after_wash <- median(Dose_after_wash)
sd_dose_after_wash <- sd(Dose_after_wash)
range_dose_after_wash <- range(Dose_after_wash)

# Create a data frame for Dose summary statistics
dose_summary <- data.frame(
  Statistic = c("Mean", "Median", "Standard Deviation", "Range (Min)", "Range (Max)"),
  Value = c(mean_dose, median_dose, sd_dose, range_dose[1], range_dose[2])
)

# Create a data frame for Dose_after_wash summary statistics
dose_after_wash_summary <- data.frame(
  Statistic = c("Mean", "Median", "Standard Deviation", "Range (Min)", "Range (Max)"),
  Value = c(mean_dose_after_wash, median_dose_after_wash, sd_dose_after_wash, range_dose_after_wash[1], range_dose_after_wash[2])
)

# Print the summary tables
cat("Summary Statistics for Dose:\n")
print(dose_summary)

cat("\nSummary Statistics for Dose_after_wash:\n")
print(dose_after_wash_summary)

#HISTOGRAMS OR DENSITY PLOTS FOR DOSE

# Load ggplot2 for plotting
library(ggplot2)

# Create a combined data frame for easier plotting
results_combined <- data.frame(
  Dose = Dose,
  Dose_after_wash = Dose_after_wash
)

# Plot histograms for Dose 
ggplot(results_combined, aes(x=Dose)) +
  geom_histogram(bins =30, fill="blue", alpha=0.7) +
  labs(title="Histogram of Dose Before Handwashing",
       x="Dose",
       y="Frequency") +
  theme_minimal()

#plot histograms for Dose_after_wash
ggplot(results_combined, aes(x=Dose_after_wash)) +
  geom_histogram(bins = 30, fill="green", alpha=0.7) +
  labs(title="Histogram of Dose After Handwashing",
       x="Dose After Handwashing",
       y="Frequency") +
  theme_minimal()

# Boxplots to identify outliers for dose 
ggplot(results_combined, aes(x=Dose)) +
  geom_boxplot() +
  labs(title="Boxplot of Dose Before Handwashing",
       x="Dose",
       y="Value") +
  theme_minimal()

# Boxplots to identify outliers for dose_after_wash
ggplot(results_combined, aes(x=Dose_after_wash)) +
  geom_boxplot() +
  labs(title="Boxplot of Dose After Handwashing",
       x="Dose",
       y="Value") +
  theme_minimal()  

# Plot density plots for Dose and Dose_after_wash
ggplot(results_combined, aes(x=Dose)) +
  geom_density(fill="blue", alpha=0.7) +
  labs(title="Density Plot of Dose Before Handwashing",
       x="Dose",
       y="Density") +
  theme_minimal()

ggplot(results_combined, aes(x=Dose_after_wash)) +
  geom_density(fill="green", alpha=0.7) +
  labs(title="Density Plot of Dose After Handwashing",
       x="Dose After Handwashing",
       y="Density") +
  theme_minimal()

# Compare the distributions before and after handwashing using density plots
ggplot(results_combined) +
  geom_density(aes(x=Dose, fill="Before Handwashing"), alpha=0.5) +
  geom_density(aes(x=Dose_after_wash, fill="After Handwashing"), alpha=0.5) +
  labs(title="Comparison of Dose Distributions Before and After Handwashing",
       x="Dose",
       y="Density",
       fill="Legend") +
  scale_fill_manual(values=c("Before Handwashing"="blue", "After Handwashing"="green")) +
  theme_minimal()

