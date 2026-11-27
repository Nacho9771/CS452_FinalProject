package com.mykitchen.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Exact hex labels from colors.jpg; change this file to personalize the whole app.
val Midnight = Color(0xFF37514D)
val Cranberry = Color(0xFFB6594C)
val Ceramic = Color(0xFFDD8E75)
val Knit = Color(0xFFEEE6DE)
val Steel = Color(0xFF90AEB2)
val Camel = Color(0xFFBE845E)

@Composable
fun KitchenTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = lightColorScheme(
        primary = Midnight, onPrimary = Color.White, secondary = Cranberry,
        background = Knit, onBackground = Midnight, surface = Color(0xFFFCFAF7),
        onSurface = Midnight, surfaceVariant = Color(0xFFE5E9E3), error = Color(0xFF9B3328),
    ), content = content)
}
