# CS 452 Final Project

------------------------------------------------------------------------

### Brainstorming Session

I first had a brainstorming session that resulted in the follwing notes:

Video Games: slay the spire ocarina of time risk of rain age of empires 2 minecraft

Politics\
Exercising\
Cooking\
I like the ocean\
facebook\
youtube\
Classical music, orchestra, conducting\
i like finding good deals

------------------------------------------------------------------------

- Addiction app

  - Make an app that you can set active to other apps
  - makes an annoying pop-up for when you open certain apps

- Build a streaming app to your home computer -find a way to be able to turn computers on remotely in order to benefit current market

- Easy recipe app

  - find recipes across the internet, searching for best rated
  - put in the main ingredients you have and result in recipe
  - filter for easy, medium, hard
  - filter for 30 mins, 60 mins, 120+ mins
  - dietary restrictions

- Game hint App

------------------------------------------------------------------------

### Initial Project Design

The refined, Android-first project proposal, ERD, system diagram, and daily goals are in [My Kitchen — Initial Project Design](INITIAL_DESIGN.md). The notes below preserve the original brainstorming and pitch; the refined design identifies the class-project scope and future features.

I am going to create a recipe app called My Kitchen. It will operate as a pantry stocker, a tailored recipe search engine based on preferences and ingredients listed, and a meal planner based on store location(s) and restricted by a budget.

Planned features include:

- Web search / LLM chatbox for recipes to create instant recipe instructions. Recipes will be decided based on:
  - Highest Ratings
  - Spices available
  - Variety from previous meal choice
  - (If applicable) requested main ingredient(s)
  - (If applicable) user specified time constraints
- All information will be stored in JSON objects in MongoDB
- IOS and android support, built in kotlin
- Cloudflare for authentication
- Redis for the middleman
  - meal plan generation jobs
  - temporary user cache
  - counter to limit AI tokens/requests, not shown to the user
- Ollama's open source model maybe (open for suggestions)
- Account Creation
  - Saves kitchen appliance inventory
  - Saves current spice inventory
  - Saves user cuisine preferences (initial screening)
  - Asks for store location information / address
  - Other ideas here
- User Preferences / Satisfaction Ratings
  - future meals based on taste/macronutrient preferences
  - If user likes complex spices, offers more complexity
  - If user likes italian, sprinkle more italian recommendations
- Set Home Store / Stores
  - Planning based on available ingredients
  - Location based pricing for meal plans
- Monthly Meal Plan Service
  - Set budget, creates meals based on budget
  - Set average time
  - Initial preferences from screening factored in first month
  - Offers one of three recipes per day for user to select (optimal choice amount)
- Ability to run on multiple applications simultaneously

------------------------------------------------------------------------

### Project Pitch

##### My Kitchen - Recipe Search and Planning Mobile App

Hey all of you middle aged moms out there, I have something that will save you time - My Kitchen. I plan to create a recipe app that stores all of your kitchen appliances, tools, spice inventory, and preferences (ratings after a meal was made) to create the easiest dinner ideas probably ever. I want to create a mobile app to use an open source LLM and web-scraping code to find the best recipes given your current ingredients that you list in a chat box. I also planned to make it prepare monthly meal plans given your budget and location.

I am interested in creating this because I spend so much time trying to find healthy and cheaper meals to prepare while still being enjoyable to eat. The other night I thawed out some chicken breasts but didn't have a recipe to make it into anything. I searched everywhere for something that seemed quick and palatable, but I ended up spending 30 minutes just to pick a teriyaki chicken recipe. On top of this, we needed to got to the store to pick up some ground ginger because we didn't have any. It was a great meal, but it made me wish for a personal chef. This app would solve the problem of making meal plans, budgeting, and looking for recipes. It would help families save money, have variety in the meals they eat, and save time shopping.

I plan to store all of the data in MongoDB, create the user interface with Kotlin, and make it accessible to multiple devices by storing everything in the cloud. I also plan to leverage Ollama's open source LLMs to calculate user preferences, find recipes tailored to the individual's history, and to create recipes based on a main ingredient or ingredients. I will store my codebase in GitHub and use CloudFlare to authenticate users. Redis will handle meal plan generation jobs, the temporary user cache, and a counter to limit the AI requests as to not overload my computer.

------------------------------------------------------------------------

## Hours Spent on Project

| Date       | What                    | Hours   |
|------------|-------------------------|---------|
| 11/17/2026 | Brainstorm Ideas        | 2       |
| 11/17/2026 | Initialize Project Code | 0.5     |
| 11/21/2026 | Project Initial Design  |         |
| **Total**  |                         | **2.5** |
