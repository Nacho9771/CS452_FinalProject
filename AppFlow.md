# Mobile App Flow

This is a description of what the app should be able to accomplish from beginning to end. I might forget some things that I have listed in the readme - if I did, infer them in the plans.

## Design Recommendations

I want it to have this color palette:

![color pallete of app](colors.jpg){width="485"}

I also want it to be very beginner chef friendly. Pinterest is a good UI to go off of for this app, as I wnat it to mimic that type of UI and functionality, mimicing all of the frontend JS and CSS styling.

## User Initialiation

The user will be met with a typical sign in or create user menu. It needs to use firebase and just connect their google account with it so they don't have to login with their own user/password. When creating an account for the first time, it will ask for their first and last name, and then it will have a cute visual with fireworks and stuff (you should think of a different thing but similar to this) and in the backend it will create an account linked to the google account (if it hasnt been already with firebase) and a celebration saying "Account Created! Hello, *first_name*!" and then it will smooth transition to "Let's get started." I want it to feel like initializing an apple product, actually lol. The app will keep them logged in, but after not using it for a few weeks it should ask them to log back in. It will then ask for details about their account on separate screens with smooth transitions in between, like the following:

(each bullet will be separated by a transition)

- Personal Address and phone number

- (using the personal address to refine store search near them), ask for stores near them. This will offer a search bar and a map so they can select the sores that are near their location. (maybe leverage google maps for this? idk). They can select up to three stores they like shopping at for groceries (for convenience of compute later).

- Ask for preferences. "Tell me: What types of foods are you most interested in cooking? Select all that apply" and then have a selection with boxes of different types of cuisine (fast, chinese, italian, american, etc.) I want this to guide the search/planner later, not be deterministic. In other words, I don't want their preferences locking them out of certain foods unless they select an checkbox saying "I would like to make recipes based only from these preferences" or something like that that would be user friendly.

- transition to "Great!" "Now we need details about your kitchen" Then ask them to select from a bunch of different tools in their kitchen with instructions on how to do so. I want this section of initialization to be a game

- they can swipe left if they have it, swipe right if they do not. it should have an undo feature, and it should also have the option to finish swiping whenever they would like to. With every appliance, I want it to save it to their account just like all of the other data involved in this. Also it should include an image of each kitchen appliance just to make sure they know it by how it looks, and also it should start with the most used (or common) kitchen appliances first and work its way down. I should probably provide a list of kitchen appliances for you to do that, so I'll come up with that later and title the file "kitchenAppliances.csv" or something like that

- After they finish with that, it should say "Thank you! Your kitchen is almost done." "Finally, we need details on what spices you already have." "Would you like to help us with your spices? This will refine your recipes and shopping " Yes/Maybe later - Finalizaation script: "Your kitchen is ready! Let's get cooking!"

## Application Features

Once the user opens the app, it will have a menubar on the bottom for them to select the application feature they need. The features are listed in subheadings below. This will mirror the menu on Robinhood's mobile application, or Facebook's top menubar.

### Find Recipes - Chatbot assisted searchbox

frontfacing UI mimics ChatGPT menu style chat

Using an LLM as a search aid, searches for recipes based on known tools, spices, and a main ingredient listed. User can specify ingredients, cuisine type, measurement type (cups/tsp/tbsp, mls, weight, etc) and should list how much time they have to cook (30mins, 60mins, 90mins, 120mins, 120+). It then searches the intenet for best rated options. Later, when they have preferences for previous recipes, it can search for recipes with ingredients they have liked before. The search tool will weigh their preferences, the ratings of the recipe, novelty (how many times they've cooked it or something similar recently) and the time to offer one recipe after the other. The user will, (similarly to dating apps or the spice/appliance inventory tool during initialization), swipe left or right on different recipes that appear so that they quickly choose somemthing they'd like to eat.

It will then create a very easy-to-follow recipe, first with the ingredients or the quantities (each ingredient adjustable from their default choice of weight to mls to cups/tsp/tbsp so it's easy to follow along), then with easy steps. Make sure to follow the recipe soecificaitons exactly though - do not change anything about it. The problem this addresses is that its really hard to choose a recipe you think you'd enjoy, have time for, and have ingredients for. It also removes all of the bloat and commplexity you have to scroll through to get to the actual recipe on recipe sites. It should include images to help the chef understand more context if available. Then the user has the option to save the recipe or rate it later (maybe the next day, maybe to be used in the calendar planner).

Later, the calendar will use this functionality to choose recipes. When choosing a recipe, the app should ask which ingredients you need or already have, and the user will check checkboxes on whether they have it or need it. it will prompt "Do you have the ingredients?" then lists the ingredients, green circle check means yes, red circle x means no. Make it colorblind friendly too.

### Calendar - meal planning calendar tool

This section will show a cute calendar style that mimics Google Calendar, but isn't as complex. By default, it will just show the recipes for dinner, but they should have the options to include breakfasts and lunches too - lunch and breakfasts will have to wait for later development.

The calendar should show the next month (4 weeks) worth of days/meals. They can have the option to go through month by month, seeing previous recipes too. In every box on the calendar, the user should be able to click on the day and see the recipe made previously. For current/future days, the user shoudl be able to tap on it and see two options - if the user has chosen a recipe for that day (or preciously planned it), then it will show the recipe and also have an option to pick a new one. IF they choose to pick a new one, it will then go through the left/right swiping sequence until they select the recipe they like. This will also be based on everything above that the search engine weighs, especially novelty or recency.

The calendar will also have an "Meal Prep" feature. In this, they should be able to specify their budget and desired store to shop at. Then, after factoring the spices and stuff they already have, it will simultaneously pick recipes based on everything about the user's data and based on the affordability of the budget and what they need to shop for. It will simultaneously search that store's inventory and pricing and compare it to recipes it wnats to select to optimize both the recipe search tool and the budget based on the amount of time they want to plan for. If this desn't make sense, tell me and we can sort out the details.

### Add Recipe / Recipe Maker

this one is basic - you should be able to add a recipe to the database and add your ingredients, steps, measuremeents, etc that comes with a recipe. This could include pictures and other stuff that recipes have. scan over online recipes to see what they usually share in common so they can be full fledged recipes.

### Your Recipes - Recipes that were favorited, saved, or have a 10/10 satisfaction rating

This is pretty straight forward - this will house previous recipes you've absolutely loved, and have a separate tab for recipes you've wanted to try. It will list them in a very friendly, pinterest type of menu so they can enter each recipe based on a photo of that recipe. You hsould also be able to put in time expected, cost, and serving size!

### Profile - Edit user settings

Users should be able to edit the following:

- personal address

- phone number

- store preferences

- kitchen appliance inventory

- spice inventory

- Preference history

People should also have a logout and delete account option. If they press the delete account option, they should be met with at least two different flags basically saying are you sure.

## Additional Considerations

The user should be able to specify the amount of people in their family (or how many people they cook for) in the account creation. That should be on its own setup page during the transitions, probably before the kitchen appliance portion.

#### Budget Calculations

The budget calculations mentioned in the calendar meal prep tool will be calculated using the stores set in the setup or in the profile section if they choose to set it up. If not, it will use approximate prices given averages in the state or something. It should web scrape from the store websites (you can build functionality that webscrapes for the exact prices after finding the html values on the webpage. You can also implement features to autoset the location when webscraping given their inputted store). This step will happen after picking a recipe, and should calculate a range per day. This is a little tricky because this implies buying ingredients per recipe, so we will have to leverage the AI model for decision making to calculate if there are any ways the user can save money (i.e. buying chicken breasts in bulk and freezing most of them instead of getting a certain amount per order). Assume shopping days and plan for the meals given the shopping days, and the user can specify the preferred shopping day or do it on their own and inform the app of a spontaneous shopping day (like a button that says "I'm shopping") for it to calculate the necessary stuff to buy that day adjusting the future shopping days within reason. Do not make it less than a week apart by auto calculations.

The budget would be for the whole household. It should recommend a budget and they should have ranges to select from. History should be tracked by the system, and maybe it should be able to generate a shopping list for you to check off. Idk if that is feasible given the scope of this project though. If this isn't that feasible, maybe make guesses as far as the budget goes and make decisions based on the individual guesses.

I would be willing to try and implement a feature so that it links to your other shopping apps and tracks the history, like an AI agent on your phone. Like, you can link walmart app, target app, etc for it to calculate your history based on what you buy. Maube this will have to wait though, omit this if its too tricky.

the flow of planning orders should be:\
find candidates → price the combined shopping list → adjust candidates → present a plan for approval

#### Recipe Add

Next, I should add that people should be able to add a recipe they have completed into the system. They should be able to either add a link to it or manually add the recipe to the app. If this is too hard right now, we should wait on implementing this step.

These receipes should default to private, but should have a publish feature that unlocks the recipe.

when making the add recipe funcitonality, it should follow this schema: <https://schema.org/Recipe>

#### Swiping

The swipe actions should be pretty straightforward - for the yes/no game, swipe right means you don't like it or don't have it or don't want it, and swipe left means the opposite. for the application on the homepage, they should be able to swipe right and left to swipe between tabs of the different functions we create (i.e. chatgpt chat, favorites, the calendar app, profile, etc.) and swiping up and down scrolls through the app function.

If the user swipes up, that means they will choose the recipe for today. It should also have a button that looks like a bookmark to save the meal for later. You can dislike or like the recipe based on a list of previous recommended recipes, and you can click a like or dislike button on the recipe like youtube on a button next to the save for later. when a user clicks on it, the icon should fill in and there should be a little animation like youtube.

when the user enters the left/right swipe game, they should not be able to swipe through the tabs unless they press the back button on the top left (or the back button found on the menubar in google phones, that button).

#### Measurements

Meausrement conversions (cups/tbsp, weight, mls, etc) should be defaulted in setup, probably on the page with the question on amount of people. On that page, you can also input the default amount of time you'd like to prepare for.

#### Serving Features

Household size supplies a default, but it can be overridden per meal if wanted. Scaling quantities is allowed under “do not change the recipe,” while cooking instructions and times remain unchanged unless supported by the source.

#### Conversion limits

Convert compatible units automatically and require an ingredient-specific conversion for weight ↔ volume. Otherwise, retain the source measurement.

#### Dietary Restrictions

In the setup part, ask if there are any dietary restrictions and provide a list of dietary restrictions for the user. Ask if you would like to plan meals around these dietary restrictions or if the user doesn't care to plan around it and wants recipes with it regardless.

#### Calendar Features

There should be explicit “Cooked,” “Skipped,” and “Moved” actions so history, ratings, pantry updates, and novelty calculations reflect what actually happened.

"Cooked" can be a faded gray over the recipe so that the recipes not cooked yet or in the future are full color while the cooked ones have a grayish filter over it (akin to other apps). Skipped should be the same as cooked but instead of gray it should be a faded different color (or something, maybe you can add something for skipped). The calendar day should have either "cooked" or "skipped" centered on the square to show that its been made. Moved should just be an option on it: wo move recipes around, they should be able to press and hold for a second (like apps on their homescreen) and move the recipe around. Once they do this, they chould be able to enter an edit mode and be able to move all of them around by dragging. to exit, they should be able to press a "save" button on the bottom, with another button to cancel if they'd like.

#### Unavailable Information

When a feature is unavailable, then there should generally be built-in defaults. If the AI isn't working, then there should be defaults. If the budget feature has issues, then there should just be a warning saying budgeting is unavailable. The app should have a troubleshoot feature to reset the UI and refresh everything to see if that will fix the problem, but it shoudl keep all of the information stored in the cache and upload it.