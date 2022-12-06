Untitled
================

## GitHub Documents

This is an R Markdown format used for publishing markdown documents to
GitHub. When you click the **Knit** button all R code chunks are run and
a markdown file (.md) suitable for publishing to GitHub is generated.

## 1.1 Reading the data

You can include R code in the document as follows:

    ## Rows: 2310 Columns: 10
    ## -- Column specification --------------------------------------------------------
    ## Delimiter: ","
    ## chr (10): ExperimentID, ParticipantID, Activity, Activity_Sub_Type, Surface,...
    ## 
    ## i Use `spec()` to retrieve the full column specification for this data.
    ## i Specify the column types or set `show_col_types = FALSE` to quiet this message.

    ## # A tibble: 2,310 x 10
    ##    experimen~1 parti~2 activ~3 activ~4 surface hand  toile~5 sex   id    surfa~6
    ##    <chr>       <chr>   <chr>   <chr>   <chr>   <chr> <chr>   <chr> <chr> <chr>  
    ##  1 YPPXM4223O  CEW005  Urinat~ <NA>    Outsid~ Right Women   Fema~ 1 CE~ Door   
    ##  2 YPPXM4223O  CEW005  Urinat~ <NA>    Cubicl~ Right Women   Fema~ 1 CE~ Cubicle
    ##  3 YPPXM4223O  CEW005  Urinat~ <NA>    Toilet~ Left  Women   Fema~ 1 CE~ Cubicle
    ##  4 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Both  Women   Fema~ 1 CE~ Person~
    ##  5 YPPXM4223O  CEW005  Urinat~ <NA>    Toilet~ Both  Women   Fema~ 1 CE~ Cubicle
    ##  6 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Left  Women   Fema~ 1 CE~ Person~
    ##  7 YPPXM4223O  CEW005  Urinat~ <NA>    Clothi~ Both  Women   Fema~ 1 CE~ Person~
    ##  8 YPPXM4223O  CEW005  Urinat~ <NA>    Flush ~ Right Women   Fema~ 1 CE~ Cubicle
    ##  9 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Left  Women   Fema~ 1 CE~ Person~
    ## 10 YPPXM4223O  CEW005  Urinat~ <NA>    Cubicl~ Right Women   Fema~ 1 CE~ Cubicle
    ## # ... with 2,300 more rows, and abbreviated variable names 1: experiment_id,
    ## #   2: participant_id, 3: activity, 4: activity_sub_type, 5: toilet_type,
    ## #   6: surface_categories

\#Frequency of surface contacts

\#\#\#Hypothesis 1: There are more surface contacts carried out in women
only toilets than men only toilets

Purpose of this is to analyse whether there is a difference in the
frequency of surface contacts made in the different toilet settings.
Does the different layouts and number of surfaces available
(i.e. urinals vs toilet seats, cubicles etc.) in the toilets influence
the frequency of contacts made by individuals? If there are more
surfaces to be encountered when using a toilet, is the individual then
touching more surfaces than they would in a different toilet layout-
what is the difference in a man unirating in a men-only toilet and in a
gender neutral toilet with regards to surface contact?

![](surface_contact_analysis_files/figure-gfm/unnamed-chunk-1-1.png)<!-- -->

    ## # A tibble: 2,310 x 10
    ##    experimen~1 parti~2 activ~3 activ~4 surface hand  toile~5 sex   id    surfa~6
    ##    <chr>       <chr>   <chr>   <chr>   <chr>   <chr> <chr>   <chr> <chr> <chr>  
    ##  1 YPPXM4223O  CEW005  Urinat~ <NA>    Outsid~ Right Women   Fema~ 1 CE~ Door   
    ##  2 YPPXM4223O  CEW005  Urinat~ <NA>    Cubicl~ Right Women   Fema~ 1 CE~ Cubicle
    ##  3 YPPXM4223O  CEW005  Urinat~ <NA>    Toilet~ Left  Women   Fema~ 1 CE~ Cubicle
    ##  4 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Both  Women   Fema~ 1 CE~ Person~
    ##  5 YPPXM4223O  CEW005  Urinat~ <NA>    Toilet~ Both  Women   Fema~ 1 CE~ Cubicle
    ##  6 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Left  Women   Fema~ 1 CE~ Person~
    ##  7 YPPXM4223O  CEW005  Urinat~ <NA>    Clothi~ Both  Women   Fema~ 1 CE~ Person~
    ##  8 YPPXM4223O  CEW005  Urinat~ <NA>    Flush ~ Right Women   Fema~ 1 CE~ Cubicle
    ##  9 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Left  Women   Fema~ 1 CE~ Person~
    ## 10 YPPXM4223O  CEW005  Urinat~ <NA>    Cubicl~ Right Women   Fema~ 1 CE~ Cubicle
    ## # ... with 2,300 more rows, and abbreviated variable names 1: experiment_id,
    ## #   2: participant_id, 3: activity, 4: activity_sub_type, 5: toilet_type,
    ## #   6: surface_categories

\#Frequency of surface contacts of each surface in different toilet
types

Here, I want to find out which surfaces the most frequently touched by
participants. Are there specific surfaces that are exclusive to certain
toilet settings? i.e Sanitary bins not available in men-only toilets
![](surface_contact_analysis_files/figure-gfm/1.3%20Frequency%20of%20contacts%20of%20each%20surfaces%20in%20different%20toilet%20types-1.png)<!-- -->

\#\#\#Hypothesis 2: There is a significant difference in frequency of
surface contacts made during urination in women-only toilets and
men-only.

\#\#\#Hypothesis 3: There is no significant difference in the frequency
of contacts made during defecation in men-only and women-only toilets

\#\#\#Hypothesis 4: There is no difference in the frequency of contacts
made during urination and defecation in gender neutral toilets between
men and women

Here I’m looking to see whether the layout of the toilet settings and
the surfaces available influences the surface contacts made during each
activity. NOTE ON MHM: Analysis can only be made between women-only and
gender neutral toilets. This is analysed further when looking at the
data on the different surfaces.

![](surface_contact_analysis_files/figure-gfm/unnamed-chunk-2-1.png)<!-- -->

    ## # A tibble: 2,310 x 10
    ##    experimen~1 parti~2 activ~3 activ~4 surface hand  toile~5 sex   id    surfa~6
    ##    <chr>       <chr>   <chr>   <chr>   <chr>   <chr> <chr>   <chr> <chr> <chr>  
    ##  1 YPPXM4223O  CEW005  Urinat~ <NA>    Outsid~ Right Women   Fema~ 1 CE~ Door   
    ##  2 YPPXM4223O  CEW005  Urinat~ <NA>    Cubicl~ Right Women   Fema~ 1 CE~ Cubicle
    ##  3 YPPXM4223O  CEW005  Urinat~ <NA>    Toilet~ Left  Women   Fema~ 1 CE~ Cubicle
    ##  4 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Both  Women   Fema~ 1 CE~ Person~
    ##  5 YPPXM4223O  CEW005  Urinat~ <NA>    Toilet~ Both  Women   Fema~ 1 CE~ Cubicle
    ##  6 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Left  Women   Fema~ 1 CE~ Person~
    ##  7 YPPXM4223O  CEW005  Urinat~ <NA>    Clothi~ Both  Women   Fema~ 1 CE~ Person~
    ##  8 YPPXM4223O  CEW005  Urinat~ <NA>    Flush ~ Right Women   Fema~ 1 CE~ Cubicle
    ##  9 YPPXM4223O  CEW005  Urinat~ <NA>    Phone   Left  Women   Fema~ 1 CE~ Person~
    ## 10 YPPXM4223O  CEW005  Urinat~ <NA>    Cubicl~ Right Women   Fema~ 1 CE~ Cubicle
    ## # ... with 2,300 more rows, and abbreviated variable names 1: experiment_id,
    ## #   2: participant_id, 3: activity, 4: activity_sub_type, 5: toilet_type,
    ## #   6: surface_categories

\#Analysing the surfaces touched in each toilet setting

### surface contacts in men only toilet

![](surface_contact_analysis_files/figure-gfm/unnamed-chunk-3-1.png)<!-- -->
\#\#\# surface contacts in women only toilet
![](surface_contact_analysis_files/figure-gfm/unnamed-chunk-4-1.png)<!-- -->
\#\#\# surface contacts in gender neutral toilet
![](surface_contact_analysis_files/figure-gfm/unnamed-chunk-5-1.png)<!-- -->
\# Comparing surface contacts with right and left hand
![](surface_contact_analysis_files/figure-gfm/unnamed-chunk-6-1.png)<!-- -->
