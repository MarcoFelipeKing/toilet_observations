#exposure.model<-function(num.people,Activity,Toilet_type){

#DEFINE THESE VARIABLES TO CHECK THINGS OUT
num.people=10
Activity="Urination"
Toilet_type="Women"
  
  require(truncdist)
  
  exposure.people<-list()
  
 # for (i in 1:num.people){ #WE ARE COMMENTING THIS OUT SO THAT WE CAN FOCUS ON GETTING THE CODE FOR 
  #1 PERSON TO RUN SMOOTHLY
  i=1
    
    #creating my "spreadsheet" and adding the events for person i in my first column
    exposure.frame<-data.frame(events=all.my.events[[i]])
    
    #determining right or left hand usage

    prob.right.hand<-hands_proportions$proportion[hands_proportions$Hand=="Right" &
                                                    hands_proportions$Toilet_type==Toilet_type]
    numbers.to.decide.hand<-runif(length(exposure.frame$events),0,1)
    
    exposure.frame$hand<-"Left"
    exposure.frame$hand[numbers.to.decide.hand<=prob.right.hand]<-"Right"
    
    #creating new columns in my "spreadsheet"-----------------------------------
    
    #Transfer efficiencies
    exposure.frame$TE.SH<-NA #surface to hand transfer efficiency
    exposure.frame$TE.HS<-NA #hand to surface transfer efficiency
    exposure.frame$TE.HM<-NA #hand to mouth transfer efficiency
    
    #Surface areas
    exposure.frame$A.hand<-NA #surface area of person's hand
    exposure.frame$A.surf<-NA #surface area of surface
    
    #Fraction of the hand used for contacts
    exposure.frame$S.h<-NA #fraction of hand surface area used for surface contacts
    exposure.frame$s.m<-NA #fraction of hand surface area used for mouth contacts
    
    #inactivation rate (decay)
    exposure.frame$inactiv<-NA
    
    #concentrations
    #exposure.frame$C.hand<-NA #concentration of virus on the hand
    exposure.frame$C.surf<-NA
    
    #exposure.frame$Door.handle.inside<-NA
    #exposure.frame$Door.handle.outside<-NA
    #exposure.frame$Cubicle.door.handle.inside<-NA
    #exposure.frame$Cubicle.door.handle.outside<-NA
    #exposure.frame$Tap<-NA
    #exposure.frame$Phone<-NA
    #exposure.frame$Flushbutton<-NA
    #exposure.frame$Soapdispenser<-NA
    #exposure.frame$Toiletsurface<-NA
    #exposure.frame$Sanitarybin<-NA
    #exposure.frame$Papertowel<-NA
    #exposure.frame$Clothing<-NA
    #exposure.frame$Skin<-NA
    #exposure.frame$Bag<-NA
    #exposure.frame$Bottle<-NA
    #exposure.frame$Toiletpaper<-NA
    #exposure.frame$Handdryer<-NA
    #exposure.frame$Binoutsidecubicle<-NA
    #exposure.frame$Doorlock<-NA
    
    #surfaces specific to MHM care
    if(Activity=="MHM"){
      exposure.frame$Menstrualcup
      exposure.frame$Sanitarypad
      exposure.frame$Tampon
    }
   
    #Column to track dose (virus transferred to mouth during face contacts)
    exposure.frame$Dose<-NA
    
    exposure.frame$position<-1:length(exposure.frame$events)
    
    #Determine the first moment of tap contact - assume that is when hands are washed.
    if(length(exposure.frame$events[exposure.frame$events=="Tap"])!=0){
      hand.wash.time<-1
      while(exposure.frame$events[hand.wash.time]!="Tap"){
        hand.wash.time<-hand.wash.time+1
      }
    }else{
      hand.wash.time<-length(exposure.frame$events)
    }
   
    
    #Start populating exposure variables in preparation for exposure model
    
    # TE: surface to hand
    
    #TE: surface to hand for metal surfaces, before hand wash
    exposure.frame$TE.SH[(exposure.frame$events=="Door handle outside" |
                         exposure.frame$events=="Door handle inside" |
                         exposure.frame$events=="Cubicle door handle inside"|
                         exposure.frame$events=="Cubicle door handle outside"|
                         exposure.frame$events=="Flush button"|
                         exposure.frame$events=="Tap"|
                         exposure.frame$events=="Door lock") & exposure.frame$position<=hand.wash.time]<-
      rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events=="Door handle outside" |
                                            exposure.frame$events=="Door handle inside" |
                                            exposure.frame$events=="Cubicle door handle inside"|
                                            exposure.frame$events=="Cubicle door handle outside"|
                                            exposure.frame$events=="Flush button"|
                                            exposure.frame$events=="Tap"|
                                            exposure.frame$events=="Door lock") 
                                         & exposure.frame$position<=hand.wash.time]),"norm",mean=0.23,sd=0.19,a=0,b=1)
    #TE: surface to hand for metal surfaces, after hand wash
    exposure.frame$TE.SH[(exposure.frame$events=="Door handle outside" |
                            exposure.frame$events=="Door handle inside" |
                            exposure.frame$events=="Cubicle door handle inside"|
                            exposure.frame$events=="Cubicle door handle outside"|
                            exposure.frame$events=="Flush button"|
                            exposure.frame$events=="Tap"|
                            exposure.frame$events=="Door lock") & exposure.frame$position>hand.wash.time]<-
      rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events=="Door handle outside" |
                                            exposure.frame$events=="Door handle inside" |
                                            exposure.frame$events=="Cubicle door handle inside"|
                                            exposure.frame$events=="Cubicle door handle outside"|
                                            exposure.frame$events=="Flush button"|
                                            exposure.frame$events=="Tap"|
                                            exposure.frame$events=="Door lock") 
                                         & exposure.frame$position>hand.wash.time]),"norm",mean=0.20,sd=0.15,a=0,b=1)
    
   #TE: surface to hand for plastic surfaces, before hand washing
   exposure.frame$TE.SH[(exposure.frame$events=="Soap dispenser"|
                           exposure.frame$events=="Bin inside the cubicle"|
                           exposure.frame$events=="Bin outside the cubicle"|
                           exposure.frame$events=="Phone"|
                           exposure.frame$events=="Toilet surface"|
                           exposure.frame$events=="Hand dryer"|
                           exposure.frame$events=="Bottle" |
                           exposure.frame$events=="Toilet brush handle") & exposure.frame$position<=hand.wash.time]<-
     rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events== "Soap dispenser"|
                                           exposure.frame$events=="Bin inside the cubicle"|
                                           exposure.frame$events=="Bin outside the cubicle"|
                                           exposure.frame$events=="Phone"|
                                           exposure.frame$events=="Toilet surface"|
                                           exposure.frame$events=="Hand dryer"|
                                           exposure.frame$events=="Bottle" |
                                           exposure.frame$events=="Toilet brush handle")
                                        & exposure.frame$position<=hand.wash.time]),"norm",mean=0.28,sd=0.23,a=0,b=1)
   
   # TE surface to hands distribution for plastics after handwashing   
   exposure.frame$TE.SH[(exposure.frame$events=="Soap dispenser"|
                           exposure.frame$events=="Bin inside the cubicle"|
                           exposure.frame$events=="Bin outside the cubicle"|
                           exposure.frame$events=="Phone"|
                           exposure.frame$events=="Toilet surface"|
                           exposure.frame$events=="Hand dryer"|
                           exposure.frame$events=="Bottle" |
                           exposure.frame$events=="Toilet brush handle") & exposure.frame$position>hand.wash.time]<-
     rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events== "Soap dispenser"|
                                           exposure.frame$events=="Bin inside the cubicle"|
                                           exposure.frame$events=="Bin outside the cubicle"|
                                           exposure.frame$events=="Phone"|
                                           exposure.frame$events=="Toilet surface"|
                                           exposure.frame$events=="Hand dryer"|
                                           exposure.frame$events=="Bottle" |
                                           exposure.frame$events=="Toilet brush handle")
                                        & exposure.frame$position>hand.wash.time]),"norm",mean=0.22,sd=0.14,a=0,b=1)

  #TE: surface to hand for polyester surfaces, irregardless of handwashing timing
exposure.frame$TE.SH[(exposure.frame$events=="Clothing"|
                        exposure.frame$events=="Bag")]<-
  rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events== "Clothing"|
                                        exposure.frame$events=="Bag")]),"norm",mean=0.3,sd=0.2,a=0,b=1)
                                     
# TE: surface to hand for paper, irregardless of handwashing timing
exposure.frame$TE.SH[(exposure.frame$events=="Paper towel"|
                        exposure.frame$events=="Toilet paper")]<-
  rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events=="Paper towel" |
                                        exposure.frame$events=="Toilet paper")]),"norm",mean=0.4,sd=0.4,a=0,b=1)
  

#TE: surface to hand for skin/, irregardless of handwashing timing
exposure.frame$TE.SH[(exposure.frame$events=="Skin"|
                        exposure.frame$events=="Hair")]<-
  rtrunc(length(exposure.frame$TE.SH[(exposure.frame$events== "SKin"|
                                        exposure.frame$events=="Hair")]),"norm",mean=0.23,sd=0.24,a=0,b=1)

#TE: Hand to surface 

#TE: hand to surface for metal surfaces, before hand wash
exposure.frame$TE.HS[(exposure.frame$events=="Door handle outside" |
                        exposure.frame$events=="Door handle inside" |
                        exposure.frame$events=="Cubicle door handle inside"|
                        exposure.frame$events=="Cubicle door handle outside"|
                        exposure.frame$events=="Flush button"|
                        exposure.frame$events=="Tap"|
                        exposure.frame$events=="Door lock") & exposure.frame$position<=hand.wash.time]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events=="Door handle outside" |
                                        exposure.frame$events=="Door handle inside" |
                                        exposure.frame$events=="Cubicle door handle inside"|
                                        exposure.frame$events=="Cubicle door handle outside"|
                                        exposure.frame$events=="Flush button"|
                                        exposure.frame$events=="Tap"|
                                        exposure.frame$events=="Door lock") 
                                     & exposure.frame$position<=hand.wash.time]),"norm",mean=0.18,sd=0.20,a=0,b=1)
#TE: hand to surface for metal surfaces, after hand wash
exposure.frame$TE.HS[(exposure.frame$events=="Door handle outside" |
                        exposure.frame$events=="Door handle inside" |
                        exposure.frame$events=="Cubicle door handle inside"|
                        exposure.frame$events=="Cubicle door handle outside"|
                        exposure.frame$events=="Flush button"|
                        exposure.frame$events=="Tap"|
                        exposure.frame$events=="Door lock") & exposure.frame$position>hand.wash.time]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events=="Door handle outside" |
                                        exposure.frame$events=="Door handle inside" |
                                        exposure.frame$events=="Cubicle door handle inside"|
                                        exposure.frame$events=="Cubicle door handle outside"|
                                        exposure.frame$events=="Flush button"|
                                        exposure.frame$events=="Tap"|
                                        exposure.frame$events=="Door lock") 
                                     & exposure.frame$position>hand.wash.time]),"norm",mean=0.22,sd=0.15,a=0,b=1)

#TE: hand to surface  for plastic surfaces, before hand washing
exposure.frame$TE.HS[(exposure.frame$events=="Soap dispenser"|
                        exposure.frame$events=="Bin inside the cubicle"|
                        exposure.frame$events=="Bin outside the cubicle"|
                        exposure.frame$events=="Phone"|
                        exposure.frame$events=="Toilet surface"|
                        exposure.frame$events=="Hand dryer"|
                        exposure.frame$events=="Bottle" |
                        exposure.frame$events=="Toilet brush handle") & exposure.frame$position<=hand.wash.time]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events== "Soap dispenser"|
                                        exposure.frame$events=="Bin inside the cubicle"|
                                        exposure.frame$events=="Bin outside the cubicle"|
                                        exposure.frame$events=="Phone"|
                                        exposure.frame$events=="Toilet surface"|
                                        exposure.frame$events=="Hand dryer"|
                                        exposure.frame$events=="Bottle" |
                                        exposure.frame$events=="Toilet brush handle")
                                     & exposure.frame$position<=hand.wash.time]),"norm",mean=0.17,sd=0.19,a=0,b=1)

# TE hand to surface distribution for plastics after handwashing   
exposure.frame$TE.HS[(exposure.frame$events=="Soap dispenser"|
                        exposure.frame$events=="Bin inside the cubicle"|
                        exposure.frame$events=="Bin outside the cubicle"|
                        exposure.frame$events=="Phone"|
                        exposure.frame$events=="Toilet surface"|
                        exposure.frame$events=="Hand dryer"|
                        exposure.frame$events=="Bottle" |
                        exposure.frame$events=="Toilet brush handle") & exposure.frame$position>hand.wash.time]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events== "Soap dispenser"|
                                        exposure.frame$events=="Bin inside the cubicle"|
                                        exposure.frame$events=="Bin outside the cubicle"|
                                        exposure.frame$events=="Phone"|
                                        exposure.frame$events=="Toilet surface"|
                                        exposure.frame$events=="Hand dryer"|
                                        exposure.frame$events=="Bottle" |
                                        exposure.frame$events=="Toilet brush handle")
                                     & exposure.frame$position>hand.wash.time]),"norm",mean=0.15,sd=0.12,a=0,b=1)

#TE: hand to surface for polyester surfaces, irregardless of handwashing timing
exposure.frame$TE.HS[(exposure.frame$events=="Clothing"|
                        exposure.frame$events=="Bag")]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events== "Clothing"|
                                        exposure.frame$events=="Bag")]),"norm",mean=0.3,sd=0.2,a=0,b=1)

# TE: hand to surface for paper, irregardless of handwashing timing
exposure.frame$TE.HS[(exposure.frame$events=="Paper towel"|
                        exposure.frame$events=="Toilet paper")]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events=="Paper towel" |
                                        exposure.frame$events=="Toilet paper")]),"norm",mean=0.4,sd=0.4,a=0,b=1)


#TE: hand to surface for skin/, irregardless of handwashing timing
exposure.frame$TE.HS[(exposure.frame$events=="Skin"|
                        exposure.frame$events=="Hair")]<-
  rtrunc(length(exposure.frame$TE.HS[(exposure.frame$events== "SKin"|
                                        exposure.frame$events=="Hair")]),"norm",mean=0.23,sd=0.24,a=0,b=1)

#TE: hand to mouth 
exposure.frame$TE.HM<- rtrunc(length(exposure.frame$TE.HM), "norm", mean=0.5, sd=0.21, a=0, b=1)

#Surface area of person's hand
exposure.frame$A.hand<-runif(1,445,535)
exposure.frame$A.surf<-runif(length(exposure.frame$events),13,641)

#concentrations on surfaces: units, Cov-2 viral loads (Amoah et al.,2021)
exposure.frame$C.surf<-runif(length(exposure.frame$C.surf),28.1,132.7)

#Surface area of the surfaces (all rounded to 1 decimal point)
#exposure.frame$A.surf[exposure.frame$events=="Bag"]
#exposure.frame$A.surf[exposure.frame$events=="Bin inside the cubicle"]<-256
#exposure.frame$A.surf[exposure.frame$events=="Bin outside the cubicle"]<-455 #only bin flap s.a
#exposure.frame$A.surf[exposure.frame$events=="Bottle"]
#exposure.frame$A.surf[exposure.frame$events=="Cubicle door handle outside"]
#exposure.frame$A.surf[exposure.frame$events=="Cubicle door handle inside"]
#exposure.frame$A.surf[exposure.frame$events=="Door handle outside"]<-459 #change to only factor in surface area of door that is touched by pps
#exposure.frame$A.surf[exposure.frame$events=="Door handle inside"]<-641
#exposure.frame$A.surf[exposure.frame$events=="Face"]
#exposure.frame$A.surf[exposure.frame$events=="Flush button"]<-9.08 
#exposure.frame$A.surf[exposure.frame$events=="Hair"]
#exposure.frame$A.surf[exposure.frame$events=="Hand dryer"]
#exposure.frame$A.surf[exposure.frame$events=="Paper towel"]
#exposure.frame$A.surf[exposure.frame$events=="Phone"]<- 82
#exposure.frame$A.surf[exposure.frame$events=="Soap dispenser"]<-26 #pump s.a
#exposure.frame$A.surf[exposure.frame$events=="Tap"]<-13
#exposure.frame$A.surf[exposure.frame$events=="Toilet brush handle"]
#exposure.frame$A.surf[exposure.frame$events=="Toilet paper"]
#exposure.frame$A.surf[exposure.frame$events=="Toilet surface"]


# FSA: front partial grip 
exposure.frame$S.h[exposure.frame$events=="Flush button"|
                     exposure.frame$events=="Skin"|
                     exposure.frame$events=="Paper towel"|
                     exposure.frame$events=="Hair"]<-runif(length(exposure.frame$S.h[exposure.frame$events=="Flush button"|
                                                                                       exposure.frame$events=="Skin"|
                                                                                       exposure.frame$events=="Paper towel"|
                                                                                       exposure.frame$events=="Hair"]), min=0.04, max=0.06)
#FSA: front partial fingers without palm
exposure.frame$S.h[exposure.frame$events=="Bin outside the cubicle"|
                     exposure.frame$events=="Toilet surface"|
                     exposure.frame$events=="Tissue paper"]<-runif(length(exposure.frame$S.h[exposure.frame$events=="Bin outside the cubicle"|
                                                                                               exposure.frame$events=="Toilet surface"|
                                                                                               exposure.frame$events=="Tissue paper"]), min=0.03, max=0.06)
#FSA: closed hand grip
exposure.frame$S.h[exposure.frame$events=="Door handle inside"|
                     exposure.frame$events=="Cubicle door handle inside"| #double check this
                     exposure.frame$events=="Phone"|
                     exposure.frame$events=="Clothing"|
                     exposure.frame$events=="Bag"|
                     exposure.frame$events=="Bottle"|
                     exposure.frame$events=="Toilet brush handle"]<-runif(length(exposure.frame$S.h[exposure.frame$events=="Door handle inside"|
                                                                                                      exposure.frame$events=="Cubicle door handle inside"| #double check this
                                                                                                      exposure.frame$events=="Phone"|
                                                                                                      exposure.frame$events=="Clothing"|
                                                                                                      exposure.frame$events=="Bag"|
                                                                                                      exposure.frame$events=="Bottle"|
                                                                                                      exposure.frame$events=="Toilet brush handle"]), min=0.1, max=0.17)
#FSA: full front palm with fingers
exposure.frame$S.h[exposure.frame$events=="Tap"|
                     exposure.frame$events=="Door handle outside"|
                     exposure.frame$events=="Cubicle door handle outside"]<-runif(length(exposure.frame$S.h[exposure.frame$events=="Tap"|
                                                                                                              exposure.frame$events=="Door handle outside"|
                                                                                                              exposure.frame$events=="Cubicle door handle outside"]), min=0.07, max=0.14)
#FSA: partial front palm without fingers
exposure.frame$S.h[exposure.frame$events=="Soap dispenser"|
                     exposure.frame$events=="Hand dryer"]<-runif(length(exposure.frame$S.h[exposure.frame$events=="Soap dispenser"|
                                                                                             exposure.frame$events=="Hand dryer"]), min = 0.03, max = 0.06)

# FSA: pinch grip
exposure.frame$S.h[exposure.frame$events=="Bin inside the cubicle"]<-runif(length(exposure.frame$S.h[exposure.frame$events=="Bin inside the cubicle"]), min=0.01, max=0.02)

# inactivation rate for metal 
exposure.frame$inactiv[(exposure.frame$events=="Door handle outside" |
                                                exposure.frame$events=="Door handle inside" |
                                                exposure.frame$events=="Cubicle door handle inside"|
                                                exposure.frame$events=="Cubicle door handle outside"|
                                                exposure.frame$events=="Flush button"|
                                                exposure.frame$events=="Tap"|
                                                exposure.frame$events=="Door lock")]<-
                          rtrunc(length(exposure.frame$inactiv[(exposure.frame$events=="Door handle outside" |
                                                                exposure.frame$events=="Door handle inside" |
                                                                exposure.frame$events=="Cubicle door handle inside"|
                                                                exposure.frame$events=="Cubicle door handle outside"|
                                                                exposure.frame$events=="Flush button"|
                                                                exposure.frame$events=="Tap"|
                                                                exposure.frame$events=="Door lock")]),"norm",median=84.29,a=54.01,b=119.56) 
                                             

#inactivation rate for plastic
exposure.frame$inactiv[(exposure.frame$events=="Soap dispenser"|
                        exposure.frame$events=="Bin inside the cubicle"|
                        exposure.frame$events=="Bin outside the cubicle"|
                        exposure.frame$events=="Phone"|
                        exposure.frame$events=="Toilet surface"|
                        exposure.frame$events=="Hand dryer"|
                        exposure.frame$events=="Bottle" |
                        exposure.frame$events=="Toilet brush handle")]<-
  rtrunc(length(exposure.frame$inactiv[(exposure.frame$events== "Soap dispenser"|
                                        exposure.frame$events=="Bin inside the cubicle"|
                                        exposure.frame$events=="Bin outside the cubicle"|
                                        exposure.frame$events=="Phone"|
                                        exposure.frame$events=="Toilet surface"|
                                        exposure.frame$events=="Hand dryer"|
                                        exposure.frame$events=="Bottle" |
                                        exposure.frame$events=="Toilet brush handle")]),"norm",mean=58.07,sd=1,a=37.76,b=81.95) #SD NEEDS TO BE REPLACED
                                     

#inactivation rate for polyester
exposure.frame$inactiv[(exposure.frame$events=="Clothing"|
                        exposure.frame$events=="Bag")]<-
  rtrunc(length(exposure.frame$inactiv[(exposure.frame$events== "Clothing"|
                                        exposure.frame$events=="Bag")]),"norm",mean=0.1,sd=1,a=0,b=1) #add values (PLACE HOLDER VALUES ADDED)

#inactivation rate for paper
exposure.frame$inactiv[(exposure.frame$events=="Paper towel"|
                        exposure.frame$events=="Toilet paper")]<-
  rtrunc(length(exposure.frame$inactiv[(exposure.frame$events=="Paper towel" |
                                        exposure.frame$events=="Toilet paper")]),"norm",mean=0.1,sd=1,a=0,b=1) #add values (PLACE HOLDER VALUES ADDED)
#inactivation rate for skin 


#Concentration on the Left Hand
exposure.frame$C.hand.L<-0

#Concentration on the Right Hand
exposure.frame$C.hand.R<-0

#Dose
exposure.frame$Dose<-0

  #EXPOSURE MODEL-------------------------------------------------------------------------------------

  for (j in 1:length(exposure.frame$events)){
 
    
    if (j==1){ 
      
      #if this is the first row... (we can't reference a previous row, because
      #row zero doesnt exist)
      
      if (exposure.frame$hand[j]=="Right"){
        
        exposure.frame$C.hand.R[j]<-exposure.frame$C.hand.R[j]+
                                    exposure.frame$C.surf[j]*exposure.frame$TE.SH[j]*exposure.frame$S.h[j]-
                                    exposure.frame$C.hand.R[j]*exposure.frame$TE.HS[j]*exposure.frame$S.h[j]
                                                                                                                                         
      }else{
        #if we use the left hand...
        exposure.frame$C.hand.L[j]<-exposure.frame$C.hand.L[j]+
          exposure.frame$C.surf[j]*exposure.frame$TE.SH[j]*exposure.frame$S.h[j]-
          exposure.frame$C.hand.L[j]*exposure.frame$TE.HS[j]*exposure.frame$S.h[j]
        
        
      }
      
    }else if (j!=1 & j!=hand.wash.time){
      #if this isn't the first moment...
      
      if(exposure.frame$hand[j]=="Right"){
        
        exposure.frame$C.hand.R[j]<-exposure.frame$C.hand.R[j-1]+
          exposure.frame$C.surf[j]*exposure.frame$TE.SH[j]*exposure.frame$S.h[j]-
          exposure.frame$C.hand.R[j-1]*exposure.frame$TE.HS[j]*exposure.frame$S.h[j]
      
        exposure.frame$C.hand.L[j]<-exposure.frame$C.hand.L[j-1]
      }else{
        #otherwise, concentration will change on left hand
        exposure.frame$C.hand.L[j]<-exposure.frame$C.hand.L[j-1]+
          exposure.frame$C.surf[j]*exposure.frame$TE.SH[j]*exposure.frame$S.h[j]-
          exposure.frame$C.hand.L[j-1]*exposure.frame$TE.HS[j]*exposure.frame$S.h[j]
        
        exposure.frame$C.hand.R[j]<-exposure.frame$C.hand.R[j-1]
      }
     
    }else{
      #not the first moment AND it is when a hand washing event occurs
      exposure.frame$C.hand.R[j]<-exposure.frame$C.hand.R[j-1]/100
      exposure.frame$C.hand.L[j]<-exposure.frame$C.hand.L[j-1]/100 #place holder hand washing efficiency
    }
    
  } # end of going through each row of my spreadsheet

plotting.frame<-data.frame(Chand=c(exposure.frame$C.hand.L,exposure.frame$C.hand.R),
                           events=rep(exposure.frame$events,2),
                           position=rep(exposure.frame$position,2),
                           hand=c(rep("Left",length(exposure.frame$events)),rep("Right",length(exposure.frame$events))))

require(ggplot2)
ggplot(plotting.frame)+geom_point(aes(x=position,y=Chand,group=hand,color=events),size=3)+
  geom_line(aes(x=position,y=Chand,linetype=hand),size=1)

# Calculate CHf (final concentration on hands) for each row in the dataframe

#exposure.frame$CHf <- exposure.frame$C.hand + exposure.frame$TE.SH * exposure.frame$S.h * exposure.frame$? - (exposure.frame$TE.SH * exposure.frame$S.h * exposure.frame$C.hand)

#conc on left hand 
#exposure.frame$CHf,<- exposure.frame$C.hand.L + exposure.frame$TE.SH * exposure.frame$S.h * exposure.frame$? - (exposure.frame$TE.SH * exposure.frame$S.h * exposure.frame$C.hand)

#conc on right hand
#exposure.frame$CHf<- exposure.frame$C.hand.R + exposure.frame$TE.SH * exposure.frame$S.h * exposure.frame$? - (exposure.frame$TE.SH * exposure.frame$S.h * exposure.frame$C.hand)

#Calculate CFf (final concentration on surface) for each row in the dataframe 
#exposure.frame$CHf<- exposure.frame$TE.SH*(exposure.frame$A.hand/exposure.frame$A.surf)* exposure.frame$?+(exposure.frame$TE.SH*exposure.frame$S.h*(exposure.frame$A.hand/exposure.frame$A.surf)*exposure.frame$C.hand) 

#Calculate CHf (final concentration on hand after hand-to-mouth)
#exposure.frame$CH<- (1-exposure.frame$TE.HM* exposure.frame$s.m)*exposure.frame$C.hand

#Calculate dose after hand to mouth contact
#exposure.frame$Dose<- exposure.frame$TE.HM*exposure.frame$s.m*exposure.frame$A.hand*exposure.frame$C.hand

# View the updated dataframe with Chf values
print(exposure.frame)


 # } #end of the loop through each person that I model
  
  
#}# end of my function