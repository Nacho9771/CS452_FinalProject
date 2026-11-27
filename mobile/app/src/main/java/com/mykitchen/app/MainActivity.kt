package com.mykitchen.app

import android.app.Activity
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.staggeredgrid.LazyVerticalStaggeredGrid
import androidx.compose.foundation.lazy.staggeredgrid.StaggeredGridCells
import androidx.compose.foundation.lazy.staggeredgrid.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.selection.selectable
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import com.mykitchen.app.data.KitchenRecipe
import com.mykitchen.app.ui.*
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            KitchenTheme {
                val model: KitchenViewModel = viewModel()
                val state by model.state.collectAsStateWithLifecycle()
                KitchenApp(state, onSignIn = { model.signIn(this) }, onRefresh = model::refresh,
                    onMore = model::loadMore, onSignOut = model::signOut)
            }
        }
    }
}

private enum class Destination(val label: String, val icon: ImageVector) {
    Find("Find Recipes", Icons.Outlined.Search),
    Calendar("Calendar", Icons.Outlined.CalendarMonth),
    Recipes("Your Recipes", Icons.Outlined.Bookmarks),
    Profile("Profile", Icons.Outlined.PersonOutline),
}

@Composable
internal fun KitchenApp(
    state: KitchenState, onSignIn: () -> Unit, onRefresh: () -> Unit,
    onMore: () -> Unit, onSignOut: () -> Unit,
) {
    val pager = rememberPagerState(initialPage = Destination.Recipes.ordinal, pageCount = { 4 })
    val scope = rememberCoroutineScope()
    var selectedRecipe by remember { mutableStateOf<KitchenRecipe?>(null) }
    // Detail mode disables horizontal destination paging. Android back returns to the library.
    BackHandler(selectedRecipe != null) { selectedRecipe = null }
    LaunchedEffect(state.signedIn) { if (!state.signedIn) selectedRecipe = null }

    Scaffold(
        containerColor = Knit,
        bottomBar = {
            BottomMenu(pager.currentPage, enabled = selectedRecipe == null) { page ->
                scope.launch { pager.animateScrollToPage(page) }
            }
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            state.error?.let { message ->
                Surface(color = MaterialTheme.colorScheme.errorContainer) {
                    Text(message, Modifier.fillMaxWidth().padding(16.dp), fontSize = 13.sp)
                }
            }
            if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth(), color = Cranberry)
            val detail = selectedRecipe
            if (detail != null) {
                RecipeDetail(detail) { selectedRecipe = null }
            } else {
                HorizontalPager(state = pager, modifier = Modifier.fillMaxSize().testTag("destinations"), key = { it }) { page ->
                    when (Destination.entries[page]) {
                        Destination.Recipes -> RecipeLibrary(state, onSignIn, onRefresh, onMore) { selectedRecipe = it }
                        Destination.Find -> FindScreen()
                        Destination.Calendar -> CalendarScreen()
                        Destination.Profile -> ProfileScreen(state, onSignIn, onSignOut)
                    }
                }
            }
        }
    }
}

@Composable
private fun BottomMenu(selected: Int, enabled: Boolean, onSelect: (Int) -> Unit) {
    Surface(color = Color(0xFFFCFAF7), shadowElevation = 8.dp) {
        Row(Modifier.fillMaxWidth().navigationBarsPadding().height(76.dp)) {
            Destination.entries.forEachIndexed { index, destination ->
                val active = index == selected
                val color = if (active) Midnight else Midnight.copy(alpha = .55f)
                Column(Modifier.weight(1f).fillMaxHeight()
                    .selectable(selected = active, enabled = enabled, role = Role.Tab, onClick = { onSelect(index) })
                    .semantics { contentDescription = destination.label },
                    horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(Modifier.width(44.dp).height(3.dp).background(if (active) Cranberry else Color.Transparent,
                        RoundedCornerShape(bottomStart = 3.dp, bottomEnd = 3.dp)))
                    Spacer(Modifier.height(12.dp))
                    Icon(destination.icon, contentDescription = null, tint = color, modifier = Modifier.size(25.dp))
                    Spacer(Modifier.height(5.dp))
                    Text(destination.label, fontSize = 11.sp, color = color,
                        fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal, maxLines = 1)
                }
            }
        }
    }
}

@Composable
private fun PageHeading(eyebrow: String, title: String, subtitle: String) {
    Column(Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 22.dp)) {
        Text(eyebrow.uppercase(), fontSize = 10.sp, letterSpacing = 2.sp, fontWeight = FontWeight.Bold, color = Cranberry)
        Spacer(Modifier.height(8.dp))
        Text(title, fontSize = 34.sp, fontFamily = FontFamily.Serif, color = Midnight, lineHeight = 38.sp)
        Spacer(Modifier.height(8.dp))
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = Midnight.copy(alpha = .75f))
    }
}

@Composable
private fun RecipeLibrary(
    state: KitchenState, onSignIn: () -> Unit, onRefresh: () -> Unit, onMore: () -> Unit,
    onRecipe: (KitchenRecipe) -> Unit,
) {
    var query by rememberSaveable { mutableStateOf("") }
    Column(Modifier.fillMaxSize()) {
        PageHeading("My Kitchen", "Your little\nrecipe collection.",
            if (state.name.isBlank()) "Good food, worth keeping." else "Good food, worth keeping. Welcome, ${state.name}.")
        if (!state.signedIn) {
            Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) { SignInCard(state.busy, onSignIn) }
        } else {
            OutlinedTextField(query, { query = it }, placeholder = { Text("Find something in your collection") },
                leadingIcon = { Icon(Icons.Outlined.Search, null) }, singleLine = true,
                shape = RoundedCornerShape(28.dp), modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp))
            Row(Modifier.fillMaxWidth().padding(horizontal = 22.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("MY RECIPES", fontSize = 11.sp, letterSpacing = 1.sp, fontWeight = FontWeight.Bold)
                TextButton(onClick = onRefresh, enabled = !state.busy) { Text("Refresh") }
            }
            val matching = state.recipes.filter { it.title.contains(query, ignoreCase = true) }
            if (matching.isEmpty()) {
                EmptyCard(Icons.Outlined.MenuBook, if (query.isBlank()) "Room for your favorites." else "No matching recipes.",
                    if (query.isBlank()) "Recipes you add to My Kitchen will appear here. Your collection stays private."
                    else "Try another recipe name, or load more of your collection.")
                if (state.nextOffset != null) TextButton(onClick = onMore, enabled = !state.busy) { Text("Load more recipes") }
            } else {
                LazyVerticalStaggeredGrid(columns = StaggeredGridCells.Fixed(2),
                    contentPadding = PaddingValues(start = 18.dp, end = 18.dp, bottom = 24.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp), verticalItemSpacing = 16.dp,
                    modifier = Modifier.weight(1f)) {
                    items(matching, key = { it.id }) { recipe -> RecipeCard(recipe, onRecipe) }
                    if (state.nextOffset != null) item {
                        TextButton(onClick = onMore, enabled = !state.busy) { Text("Load more") }
                    }
                }
            }
        }
    }
}

@Composable
private fun RecipeCard(recipe: KitchenRecipe, onRecipe: (KitchenRecipe) -> Unit) {
    val height = if (recipe.id.hashCode() % 2 == 0) 210.dp else 170.dp
    Column(Modifier.clip(RoundedCornerShape(18.dp)).clickable { onRecipe(recipe) }) {
        Box(Modifier.fillMaxWidth().height(height).clip(RoundedCornerShape(18.dp)).background(Steel.copy(alpha = .4f))) {
            Icon(Icons.Outlined.Restaurant, null, tint = Midnight.copy(alpha = .35f),
                modifier = Modifier.align(Alignment.Center).size(42.dp))
            if (recipe.imageUrl != null) AsyncImage(model = recipe.imageUrl, contentDescription = recipe.title,
                contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            Surface(Modifier.align(Alignment.BottomStart).padding(10.dp), color = Color(0xFFF9F5EF), shape = RoundedCornerShape(20.dp)) {
                Text("${recipe.prepMinutes + recipe.cookMinutes} min prep + cook", fontSize = 10.sp,
                    modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp))
            }
        }
        Text(recipe.title, fontSize = 16.sp, fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(top = 9.dp, start = 3.dp), maxLines = 3, overflow = TextOverflow.Ellipsis)
        Text("${recipe.servings} servings · Private", fontSize = 11.sp, color = Midnight.copy(alpha = .65f),
            modifier = Modifier.padding(top = 4.dp, start = 3.dp))
    }
}

@Composable
private fun SignInCard(busy: Boolean, onSignIn: () -> Unit) {
    Surface(Modifier.fillMaxWidth().padding(20.dp), shape = RoundedCornerShape(24.dp), color = Midnight) {
        Column(Modifier.padding(26.dp)) {
            Icon(Icons.Outlined.RestaurantMenu, null, tint = Ceramic, modifier = Modifier.size(42.dp))
            Spacer(Modifier.height(20.dp))
            Text("Make yourself\nat home.", fontFamily = FontFamily.Serif, fontSize = 30.sp, color = Knit)
            Text("Sign in to bring your kitchen and private recipes with you.", color = Knit,
                modifier = Modifier.padding(vertical = 16.dp))
            Button(onClick = onSignIn, enabled = !busy,
                colors = ButtonDefaults.buttonColors(containerColor = Knit, contentColor = Midnight)) {
                Text("Continue with Google")
            }
        }
    }
}

@Composable
private fun EmptyCard(icon: ImageVector, title: String, description: String) {
    Surface(Modifier.padding(20.dp).fillMaxWidth(), color = Color(0xFFFCFAF7), shape = RoundedCornerShape(22.dp)) {
        Column(Modifier.padding(26.dp)) {
            Icon(icon, null, tint = Cranberry, modifier = Modifier.size(32.dp))
            Text(title, fontFamily = FontFamily.Serif, fontSize = 24.sp, modifier = Modifier.padding(vertical = 12.dp))
            Text(description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun RecipeDetail(recipe: KitchenRecipe, onBack: () -> Unit) {
    LazyColumn(contentPadding = PaddingValues(bottom = 24.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(12.dp)) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back to Your Recipes") }
                Text("YOUR RECIPE", fontSize = 11.sp, letterSpacing = 2.sp)
            }
            if (recipe.imageUrl != null) AsyncImage(recipe.imageUrl, recipe.title, contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxWidth().height(280.dp))
            PageHeading("${recipe.servings} servings · ${recipe.prepMinutes + recipe.cookMinutes} min prep + cook",
                recipe.title, recipe.description)
            Text("Ingredients", fontSize = 25.sp, fontFamily = FontFamily.Serif, modifier = Modifier.padding(24.dp, 12.dp))
        }
        items(recipe.ingredients) { ingredient ->
            Text("•  ${ingredient.originalText}", modifier = Modifier.padding(horizontal = 24.dp, vertical = 8.dp))
        }
        item { Text("Let's make it", fontSize = 25.sp, fontFamily = FontFamily.Serif, modifier = Modifier.padding(24.dp, 20.dp)) }
        items(recipe.steps.size) { index ->
            Row(Modifier.padding(horizontal = 24.dp, vertical = 12.dp)) {
                Text("${index + 1}", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Cranberry, modifier = Modifier.width(36.dp))
                Text(recipe.steps[index], lineHeight = 25.sp)
            }
        }
        if (recipe.equipment.isNotEmpty()) item {
            Text("Equipment: ${recipe.equipment.joinToString()}", modifier = Modifier.padding(24.dp))
        }
        recipe.sourceUrl?.let { source -> item {
            val context = LocalContext.current
            TextButton(onClick = {
                context.startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(source)))
            }, modifier = Modifier.padding(horizontal = 16.dp)) { Text("View original recipe") }
        } }
    }
}

@Composable
private fun FindScreen() {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        PageHeading("A little inspiration", "What sounds\ngood tonight?", "Start with what's in your kitchen.")
        EmptyCard(Icons.Outlined.AutoAwesome, "Dinner ideas, made for you.",
            "Personalized recipe discovery is coming next. For now, browse the recipes you've already collected.")
    }
}

@Composable
private fun CalendarScreen() {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        PageHeading("Make room for good food", "A week to\nlook forward to.", "Your dinners, all in one place.")
        EmptyCard(Icons.Outlined.CalendarMonth, "Your table is taking shape.",
            "Meal scheduling is coming next. Your saved recipes will be ready when you plan your dinners.")
    }
}

@Composable
private fun ProfileScreen(state: KitchenState, onSignIn: () -> Unit, onSignOut: () -> Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        PageHeading("Your corner", if (state.name.isBlank()) "Your kitchen,\nyour way." else "Hello, ${state.name}.",
            "A little more you in every meal.")
        if (!state.signedIn) SignInCard(state.busy, onSignIn)
        else {
            EmptyCard(Icons.Outlined.PersonOutline, "You're at home here.",
                "Your account and private recipes are connected. Kitchen setup and preference editing are coming next.")
            OutlinedButton(onClick = onSignOut, enabled = !state.busy, modifier = Modifier.padding(horizontal = 24.dp)) { Text("Sign out") }
        }
    }
}

@Preview(showBackground = true, widthDp = 390, heightDp = 844)
@Composable
private fun KitchenNavigationPreview() {
    KitchenTheme { KitchenApp(KitchenState(), {}, {}, {}, {}) }
}
