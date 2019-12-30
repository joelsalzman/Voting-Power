# Where do votes matter most?
This project looks at where votes have mattered most in US federal elections since 1999. In this repository, you'll find all the code involved in the analysis, most of the data, and some of the results.

## How to answer the question
How do we tell where votes matter most from a geographic perspective? By looking at where the margins have been closest in various elections. For instance, an election with a margin of 0 -- a tie -- is where a vote matters the most. So in order to figure out where votes matter most, we need to answer the following question:

1) Where have elections been the closest?
2) Which elections took place where?
3) Which elections matter?

Let's start with the first question. Answering this is simply a matter of finding out how much the winner won by in every election. Three of the tables in this repo begin with "1976-2018," which contain election data from all the House, Senate, and presidential elections since 1976. The tables with "margin" in their names contain the raw (number of votes the winner won by) and decimal (the proportion of votes the winner won by) margins in each of those elections.

Determining the geospatial aspect of these elections is a little harder. Votes in federal elections are counted either from a statewide or districtwide vote tally. However, district lines change. You could be in District 1 for ten years and then one day, the map is redrawn and now you're in District 3. Assuming you don't move, we need a way to reflect that you voted in District 1 elections until a given year and then in District 3 elections after that. The way to do that is by overlaying all the maps of congressional districts. Each polygon in the yearly maps represents a congressional district. Each polygon in the overlay represents a region of land that was in a unique set of congressional districts between 1999 and 2019. For instance, the polygon containing your house would have the attributes of being in District 1 from 1999 until, say, 2010, and being in District 3 from 2011 to 2019.

Finally, we need to define which elections matter. This project looks at three types of elections: House, Senate, and Presidency. While people generally think of the presidential election as the most important, there are convincing arguments to be made for the importance of all three. The way to quantify the importance of each election is with a "utility value," which is a number between 0 and 1 that represents relatively how important a vote in that individual election was. A 1 means that one vote was as important as possible; the tally was a tie. A 0 means that one vote was as unimportant as possible. The way I determined that was by finding the worst historical margin for an election of that type to use as a denominator. Each polygon received a utility value for raw and decimal margins in House, Senate, and presidential races by taking the average margin in every election that occurred in the region of land and normalizing it. In addition to the six individual utility values, each polygon also received a combined utility value, which is the result of combining the other three. I chose to weight the three types of elections equally, but different weighting schemes would result in different combined utility values.

The final combined utility values represent how much votes mattered in that place between 1999 and 2019.

## The Process
1) Acquire and clean the data
2) Calculate the margins in each relevant election
3) Overlay maps of the congressional districts drawn between 1999 and 2019
4) Merge the voting data with the geodata
5) Calculate utility values
6) Publish results

## The Results
There are eight sets of results to look at. I'll include a small discussion here about a few interesting results and hopefully soon have the interactive map up so that anyone who finds this page can explore the data themselves. For now, hang tight.

## Credits
The first incarnation of this project was done in Spring 2019 as part of GEOG 176C at UCSB as a group project between Juan Miranda, Owen Karlenzig, and myself. The shapefiles were supplied by the STKO Lab at UCSB, led by Krysztof Janowicz (who was also the instructor for that class).

The project you see here was done entirely by myself, save for two shapefiles (CGDs 115 and 116) provided by the STKO Lab. The voting data come from the MIT Election Lab and the other CGD shapefiles come directly from USGS.

I redid the project for a few reasons. First, because we had to finish the project in time for the end of the term, I wasn't fully satisfied with the results. The previous version included the same analysis of voting data but handled the geospatial aspect in a much more simplistic way. Second, I wanted to use different tools. I wrote all the code for the previous version in R, but I much prefer Python, so I did this version in Python. We also used ArcGIS before, but I did this entirely with open source software (QGIS, PostgreSQL, and OpenLayers).
