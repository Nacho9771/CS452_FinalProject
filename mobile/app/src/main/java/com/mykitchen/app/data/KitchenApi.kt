package com.mykitchen.app.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

data class Ingredient(val name: String, val originalText: String)
data class KitchenRecipe(
    val id: String, val title: String, val description: String, val servings: Int,
    val prepMinutes: Int, val cookMinutes: Int, val imageUrl: String?,
    val ingredients: List<Ingredient>, val steps: List<String>, val equipment: List<String>,
    val sourceUrl: String?, val raw: JSONObject,
)
data class RecipePage(val recipes: List<KitchenRecipe>, val nextOffset: Int?)

class ApiException(val status: Int, val requestId: String?, message: String) : IOException(message)

class KitchenApi(private val baseUrl: String) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS).readTimeout(20, TimeUnit.SECONDS).build()

    // Network work stays off the UI thread. Tokens appear only in request headers.
    private suspend fun request(path: String, token: String, body: JSONObject? = null): JSONObject =
        withContext(Dispatchers.IO) {
            val request = Request.Builder().url(baseUrl.trimEnd('/') + path)
                .header("Authorization", "Bearer $token")
                .apply { if (body != null) post(body.toString().toRequestBody("application/json".toMediaType())) }
                .build()
            client.newCall(request).execute().use { response ->
                val result = JSONObject(response.body?.string() ?: "{}")
                if (!response.isSuccessful) {
                    throw ApiException(response.code, response.header("X-Request-ID"),
                        result.optString("detail", "The request could not be completed."))
                }
                result
            }
        }

    suspend fun account(token: String): JSONObject = request("/api/v1/account", token, JSONObject())

    suspend fun recipes(token: String, offset: Int = 0): RecipePage {
        val response = request("/api/v1/recipes?offset=$offset&limit=20", token)
        val items = response.getJSONArray("items")
        return RecipePage((0 until items.length()).map { parseRecipe(items.getJSONObject(it)) },
            if (response.isNull("next_offset")) null else response.getInt("next_offset"))
    }

    companion object {
        fun parseRecipe(record: JSONObject): KitchenRecipe {
            val recipe = record.getJSONObject("recipe")
            val ingredients = recipe.getJSONArray("ingredients")
            fun strings(key: String): List<String> {
                val array = recipe.optJSONArray(key) ?: return emptyList()
                return (0 until array.length()).map { array.getString(it) }
            }
            return KitchenRecipe(
                id = record.getString("id"), title = recipe.getString("title"),
                description = recipe.optString("description"), servings = recipe.getInt("servings"),
                prepMinutes = recipe.getInt("prep_minutes"), cookMinutes = recipe.getInt("cook_minutes"),
                imageUrl = strings("image_urls").firstOrNull(),
                ingredients = (0 until ingredients.length()).map {
                    val item = ingredients.getJSONObject(it)
                    Ingredient(item.getString("name"), item.getString("original_text"))
                }, steps = strings("steps"), equipment = strings("equipment"),
                sourceUrl = if (recipe.isNull("source_url")) null else recipe.optString("source_url").ifBlank { null },
                raw = recipe,
            )
        }
    }
}
