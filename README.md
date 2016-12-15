# Distributions of grades from Blackboard Learn
View grades distribution for University of Toronto course MAT194 F 2016. Get an idea of where students stand in their respective sections, which are graded differently.
- Python flask server framework
- Data is updated from portal.utoronto.ca by web scraping
- Grades sent to client are anonymous across different tests, therefore contain no sensitive information
- Simple Bootstrap main page, with Plotly distribution graph

[See it in action.](https://mat194.herokuapp.com) The page will likely take a few seconds to load up the on your first visit because Heroku's free tier puts the server to sleep when inactive and needs to reboot it for a new visitor.

## TODO
- Refactor data pull from Portal as worker job
