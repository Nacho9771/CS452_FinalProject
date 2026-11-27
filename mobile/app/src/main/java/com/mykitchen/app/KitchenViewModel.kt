package com.mykitchen.app

import android.app.Activity
import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.mykitchen.app.auth.GoogleSession
import com.mykitchen.app.data.KitchenApi
import com.mykitchen.app.data.KitchenRecipe
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class KitchenState(
    val signedIn: Boolean = false, val busy: Boolean = false, val name: String = "",
    val recipes: List<KitchenRecipe> = emptyList(), val nextOffset: Int? = null,
    val error: String? = null,
)

class KitchenViewModel(application: Application) : AndroidViewModel(application) {
    private val session = GoogleSession(application)
    private val api = KitchenApi(BuildConfig.API_BASE_URL)
    private val mutableState = MutableStateFlow(KitchenState(signedIn = session.signedIn))
    val state = mutableState.asStateFlow()

    init { if (session.signedIn) refresh() }

    fun signIn(activity: Activity) = runAction {
        session.signIn(activity)
        mutableState.update { it.copy(signedIn = true) }
        load()
    }

    fun refresh() = runAction { load() }

    private suspend fun load() {
        val token = session.token()
        val account = api.account(token)
        val page = api.recipes(token)
        val firstName = account.getJSONObject("profile").optString("first_name")
        mutableState.update { it.copy(
            signedIn = true, name = firstName.ifBlank { session.displayName?.substringBefore(' ') ?: "" },
            recipes = page.recipes, nextOffset = page.nextOffset,
        ) }
    }

    fun loadMore() = runAction {
        val offset = mutableState.value.nextOffset ?: return@runAction
        val page = api.recipes(session.token(), offset)
        mutableState.update { it.copy(recipes = (it.recipes + page.recipes).distinctBy { recipe -> recipe.id }, nextOffset = page.nextOffset) }
    }

    fun signOut() = runAction {
        // Clear displayed private data immediately, even if credential-provider cleanup fails.
        mutableState.value = KitchenState(busy = true)
        session.signOut()
    }

    private fun runAction(action: suspend () -> Unit) {
        if (mutableState.value.busy) return
        mutableState.update { it.copy(busy = true, error = null) }
        viewModelScope.launch {
            try { action() }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (error: Exception) { mutableState.update { it.copy(error = error.message ?: "Something went wrong. Please try again.") } }
            finally { mutableState.update { it.copy(busy = false) } }
        }
    }
}
