# Where do votes matter most?
This project looks at where votes have mattered most in US federal elections since 1999. In this repository, you'll find all the code to run the analysis on your own in addition to the results.

# The Process Explained
How do we tell where votes matter most from a geographic perspective? By looking at where the margins have been closest in various elections. For instance, an election with a margin of 0 -- a tie -- is where a vote matters the most. Three of the tables in this repo begin with "1976-2018"; those contain election data from all the House, Senate, and presidential elections since 1976. The tables with "margin" in their names contain the raw (number of votes the winner won by) and decimal (the proportion of votes the winner won by) margins in each of those elections. That says which elections were the closest, which tells us something about which votes mattered most. But we're not done yet.

District lines change. You could be in District 1 for ten years and then suddenly, your local politicians change the map and now you're in District 3. Assuming you don't move, we need a way to reflect that you voted in District 1 elections until a given year and then in District 3 elections after that. The way to do that is by overlaying all the maps of congressional districts. The polygon on the map that you live inside of will have the attributes of being in District 1 for however many years until it was changed, and being in District 3 after that. Now we can tell which elections you would've voted in, which will tell us more about how much your vote mattered.

In order to compare one region of land to another, the margins have to be normalized. First we take the average margin for each type of election from 1999 to 2019. Then we normalize it according to the worst recorded margin for that type of election. What comes out is a value between 0 and 1, where 1 means that the election was a tie (so your vote matters immensely) and 0 means that the election had the greatest possible margin (so your vote mattered as little as possible).

Finally, we need to define what it means for a vote to matter. This project looks at three types of elections: House, Senate, and Presidency. So there are three "utility values" between 0 and 1 that represent how much a vote mattered in a given region of land in House, Senate, and presidential elections respectively. The final step is to combine those three into a single value that represents the overall utility of a vote in that place.

# The Results
Currently there are no results. Hang tight.
