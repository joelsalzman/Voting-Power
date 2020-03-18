# [CLICK HERE FOR INTERACTIVE MAP](https://joelsalzman.github.io/gdvp.html)



# Where do votes matter most?
This project looks at where votes have mattered most in US federal elections since 1999. This repo contains all the code and most of the data.

## How to answer the question
How do we tell where votes matter most from a geographic perspective? By looking at where the margins have been closest in various elections. For instance, an election with a margin of 0 (a tie) is where a vote matters the most. So in order to answer the question, we need to figure out the following:

1) Where have elections been the closest?
2) Which elections took place where?
3) Which elections matter?

Let's start with the first question. Answering this is simply a matter of finding out how much the winner won by in every election. The three tables in this repo whose names begin with "1976-2018" contain election data from all the House, Senate, and presidential elections since 1976. The tables with "margin" in their names contain the raw (number of votes the winner won by) and decimal (the proportion of votes the winner won by) margins in each of those elections.

Determining the geospatial aspect of these elections is a little harder. Votes in federal elections are counted either from a statewide or districtwide vote tally. However, district lines change. You could be in District 1 for ten years and then one day, the map is redrawn and now you're in District 3. Assuming you don't move, we need a way to reflect that you voted in District 1 elections until a given year and then in District 3 elections after that. The way to do that is by overlaying all the maps of congressional districts in that timeframe. Each polygon in the yearly maps represents a congressional district; each polygon in the overlay represents a region of land that was in a unique set of congressional districts between 1999 and 2019. For instance, the polygon containing your house would have the attributes of being in District 1 from 1999 until, say, 2010, and being in District 3 from 2011 to 2019. Fortunately, state boundaries haven't changed since 1999, so this only affects House races.

Finally, we need to define how much different elections matter. This project looks at three types of elections: House, Senate, and Presidency. While people generally think of the presidential election as the most important, there are convincing arguments to be made for the importance of all three. The way to quantify the importance of an election is with a "utility value," which is a number between 0 and 1 that represents relatively how important a vote in that individual election was. Each polygon received a utility value for raw and decimal margins in House, Senate, and presidential races by taking the average margin in every election that occurred in the region of land and normalizing it. In addition to the six individual utility values, each polygon also received a combined utility value, which is the result of combining the other three.

The final combined utility values represent how much votes mattered in that place between 1999 and 2019.

> *The Process:*
> 1) Acquire and clean the data
> 2) Calculate the margins in each relevant election
> 3) Overlay maps of the congressional districts drawn between 1999 and 2019
> 4) Merge the voting data with the geodata
> 5) Calculate utility values
> 6) Publish results

## Utility values
A utility value represents how "good" something is. In this context, a 1 means that one vote was as important as possible. In other words, the tally was a tie. A 0 means that one vote was as unimportant as possible. The way I determined what a 0 should be was by finding the greatest historical margin for an election of that type. That way, every value is between 0 and 1, and the lower values represent places with closer average election margins.

Due to the Electoral College, not every state is equally important to win. Presidential utility values had to be scalar multiplied by the number of eligible electors in that state. So the presidential utility values of polygons in California were multiplied by 55, those in Wyoming by 3, etc. Nebraska and Maine also have special rules since they allocate two electors to the winner of the statewide popular vote and one elector to the winner of each districtwide popular vote, so both vote tallies had to be taken into account.

Since each seat in Congress has the same power (geographically speaking), House and Senate utility values didn't have to change.

## Results
The best place in the country to vote in the past twenty years was in Nevada, around the southern part of Las Vegas. Nevada's fairly small population is politically heterogeneous, which leads the thin margins in most races. New Hampshire was the second best and New Mexico was the third best. In many ways, this disputes the convential wisdom regarding swing states. The main reason why the best states to vote aren't necessarily the purplest is that there is an important distinction between where it is good to vote and where it makes the most sense to commit resources. The latter is a question asked during each election, while the former is a primarily academic question.

Washington DC was the worst place to vote because DC residents don't have voting representation in Congress. The next two worst were California and New York, both of which rank poorly due to their massive populations and the dominance of the Democratic party. Nebraska also fares poorly because it is so solidly Republican despite its relatively small population. Notably, while Alabama is very uncompetitive overall, Georgia contains numerous regions with consistently close elections. 

The results for individual race types are more intuitive. For presidential elections, Florida is the undisputed winner. Senate margins tend to mirror presidential margins, and are primarily a function of partisanship and population. House margins are far more geographically varied because of the equal population requirement, so they reflect partisanship rather than population.

You can explore some of the data on my [website](joelsalzman.github.io/gdvp.html).

## Credits
The first incarnation of this project was done in Spring 2019 as part of GEOG 176C at UCSB as a group project between [Juan Miranda](https://www.linkedin.com/in/juan-miranda-61a958138/), [Owen Karlenzig](https://www.linkedin.com/in/owen-karlenzig-95890a154/), and [myself](https://www.linkedin.com/in/joel-salzman-322891156/). The shapefiles were supplied by the [STKO Lab at UCSB](https://stko.geog.ucsb.edu/), led by Krysztof Janowicz (who was also the instructor for that class). The poster for the group project is [here](https://drive.google.com/file/d/1mxGxF_O4GJmrZ8ctpUhaFUgVHSbkkc6g/view).

The project you see in this repo was done entirely by myself, save for two shapefiles (CGDs 115 and 116) provided by the STKO Lab. The voting data come from the MIT Election Lab, the State Boards of Maine and Nebraska (aggregated during the previous incarnation of the project), and the other CGD shapefiles come directly from USGS. It was done in Python using geopandas and a [shapely version of ST_MakeValid](https://github.com/ftwillms/makevalid), visualized in QGIS, and implemented online with Leaflet and JQuery.
