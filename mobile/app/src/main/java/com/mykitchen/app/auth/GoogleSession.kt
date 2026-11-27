package com.mykitchen.app.auth

import android.app.Activity
import android.content.Context
import androidx.credentials.ClearCredentialStateRequest
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.NoCredentialException
import androidx.credentials.exceptions.GetCredentialCancellationException
import kotlinx.coroutines.CancellationException
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.google.firebase.FirebaseApp
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.GoogleAuthProvider
import kotlinx.coroutines.tasks.await

class GoogleSession(private val context: Context) {
    private val firebaseApp = FirebaseApp.initializeApp(context)
    private val auth: FirebaseAuth? = firebaseApp?.let { FirebaseAuth.getInstance(it) }
    val signedIn: Boolean get() = auth?.currentUser != null
    val displayName: String? get() = auth?.currentUser?.displayName

    suspend fun signIn(activity: Activity) {
        val clientIdResource = context.resources.getIdentifier("default_web_client_id", "string", context.packageName)
        check(auth != null && clientIdResource != 0) { "Google sign-in is not configured for this build. See docs/MOBILE.md." }
        val option = GetSignInWithGoogleOption.Builder(context.getString(clientIdResource)).build()
        val result = try {
            CredentialManager.create(activity).getCredential(activity,
                GetCredentialRequest.Builder().addCredentialOption(option).build())
        } catch (error: NoCredentialException) {
            error("Add a Google account to this emulator or phone, then try again.")
        } catch (error: GetCredentialCancellationException) {
            throw CancellationException("Sign-in cancelled", error)
        }
        val credential = result.credential
        check(credential is CustomCredential && credential.type == GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL) {
            "Google sign-in did not return the expected credential."
        }
        val google = GoogleIdTokenCredential.createFrom(credential.data)
        auth.signInWithCredential(GoogleAuthProvider.getCredential(google.idToken, null)).await()
    }

    suspend fun token(): String = checkNotNull(auth?.currentUser) { "Please sign in." }
        .getIdToken(false).await().token ?: error("Please sign in again.")

    suspend fun signOut() {
        auth?.signOut()
        CredentialManager.create(context).clearCredentialState(ClearCredentialStateRequest())
    }
}
