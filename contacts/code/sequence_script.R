

df$SurfaceCategories[df$Surface=="Cubicle door handle inside" |
                       df$Surface=="Cubicle door handle outside"]<-"Entry/Exit"

#sets up my custom function in R so that R knows what to do if I
#reference the function
source("contacts/code/sequence_function.R")

mc_female_ss_urination_cubicle  <- create_markov_chain(df, "Female", "Urination", "Women", num.people=10000, file_name='mc_female_ss_urination_cubicle_10000')# add num.people for each subset
#mc_female_ss_urination_hygiene <- create_markov_chain(df, "Female", "Urination", "Women", num.people=10,)
mc_female_ss_defecation_cubicle <- create_markov_chain(df, "Female", "Defecation", "Women", num.people=10000, file_name='mc_female_ss_defecation_cubicle_10000')
#mc_female_ss_defecation_hygiene <- create_markov_chain(df, "Female", "Defecation", "Women", "Hygiene")
mc_female_ss_mhm_cubicle <- create_markov_chain(df, "Female", "MHM", "Women", num.people=10000, file_name='mc_female_ss_mhm_cubicle_10000')
#mc_female_ss_mhm_hygiene <- create_markov_chain(df, "Female", "MHM", "Women", "Hygiene")
mc_male_ss_defecation_cubicle <- create_markov_chain(df, "Male", "Defecation", "Men", num.people=10000, file_name='mc_male_ss_defecation_cubicle_10000')
#mc_male_ss_defecation_hygiene <- create_markov_chain(df, "Male", "Defecation", "Men", "Hygiene")
mc_female_gn_urination_cubicle <- create_markov_chain(df, "Female", "Urination", "Gender neutral", num.people=10000, file_name='mc_female_gn_urination_cubicle_10000')
#mc_female_gn_urination_hygiene <- create_markov_chain(df, "Female", "Urination", "Gender neutral", "Hygiene")
mc_female_gn_defecation_cubicle <- create_markov_chain(df, "Female", "Defecation", "Gender neutral", num.people=10000, file_name='mc_female_gn_defecation_cubicle_10000')
#mc_female_gn_defecation_hygiene <- create_markov_chain(df, "Female", "Defecation", "Gender neutral", "Hygiene")
mc_female_gn_mhm_cubicle <- create_markov_chain(df, "Female", "MHM", "Gender neutral", num.people=10, file_name='mc_female_gn_mhm_cubicle_10')
#mc_female_gn_mhm_hygiene <- create_markov_chain(df, "Female", "MHM", "Gender neutral", "Hygiene")
mc_male_gn_urination_cubicle <- create_markov_chain(df, "Male", "Urination", "Gender neutral", num.people=10000, file_name='mc_male_gn_urination_cubicle_10000')
#mc_male_gn_urination_hygiene <- create_markov_chain(df, "Male", "Urintation", "Gender neutral", "Hygiene")
mc_male_gn_defecation_cubicle <- create_markov_chain(df, "Male", "Defecation", "Gender neutral", num.people=10000, file_name='mc_male_gn_defecation_cubicle_10000')
#mc_male_gn_defecation_hygiene <- create_markov_chain(df, "Male", "Defecation", "Gender neutral", "Hygiene")
mc_male_ss_urination_hygiene <- create_markov_chain(df, "Male", "Urination", "Men", num.people=10000, file_name='mc_male_ss_urination_cubicle_10000')


#

