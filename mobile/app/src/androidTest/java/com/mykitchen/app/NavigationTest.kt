package com.mykitchen.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.mykitchen.app.ui.KitchenTheme
import com.mykitchen.app.data.Ingredient
import com.mykitchen.app.data.KitchenRecipe
import org.json.JSONObject
import org.junit.Rule
import org.junit.Test

class NavigationTest {
    @get:Rule val compose = createComposeRule()

    @Test fun bottomTabsSelectDestinationsAndSwipesStayInSync() {
        compose.setContent { KitchenTheme { KitchenApp(KitchenState(), {}, {}, {}, {}) } }
        compose.onNodeWithContentDescription("Your Recipes").assertIsSelected()
        compose.onNodeWithContentDescription("Calendar").performClick()
        compose.onNodeWithContentDescription("Calendar").assertIsSelected()
        compose.onNodeWithTag("destinations").performTouchInput { swipeLeft() }
        compose.onNodeWithContentDescription("Your Recipes").assertIsSelected()
        compose.onNodeWithContentDescription("Profile").performClick()
        compose.onNodeWithContentDescription("Profile").assertIsSelected()
        compose.onNodeWithContentDescription("Find Recipes").performClick()
        compose.onNodeWithContentDescription("Find Recipes").assertIsSelected()
    }

    @Test fun recipeDetailsKeepSourceTextAndRequireBackBeforeChangingTabs() {
        val recipe = KitchenRecipe("test-recipe", "Test soup", "A test fixture", 2,
            10, 20, null, listOf(Ingredient("water", "2 cups water")),
            listOf("Simmer for 20 minutes."), emptyList(), null, JSONObject())
        compose.setContent {
            KitchenTheme { KitchenApp(KitchenState(signedIn = true, recipes = listOf(recipe)), {}, {}, {}, {}) }
        }
        compose.onNodeWithText("Test soup").performClick()
        compose.onNodeWithContentDescription("Calendar").assertIsNotEnabled()
        compose.onNodeWithTag("destinations").assertDoesNotExist()
        compose.onNodeWithText("•  2 cups water").assertExists()
        compose.onNodeWithContentDescription("Back to Your Recipes").performClick()
        compose.onNodeWithContentDescription("Calendar").assertIsEnabled().performClick()
        compose.onNodeWithContentDescription("Calendar").assertIsSelected()
    }
}
