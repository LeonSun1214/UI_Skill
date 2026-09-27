import 'package:flutter/material.dart';

/// The palette every scheme is built from.
class AppColors {
  static const pine = Color(0xFF1F5C45);
  static const moss = Color(0xFF8DB596);
  static const granite = Color(0xFF9E9E9E);
  static const snow = Color(0xFFFFFFFF);
  static const night = Color(0xFF121212);
  static const ember = Color(0xFFC2410C);
}

/// Spacing steps: widgets use these, not bare numbers.
class Insets {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
}

class AppTheme {
  static const lightScheme = ColorScheme(
    brightness: Brightness.light,
    primary: AppColors.pine,
    onPrimary: AppColors.snow,
    secondary: AppColors.moss,
    onSecondary: Color(0xFF10261C),
    error: AppColors.ember,
    onError: AppColors.snow,
    surface: AppColors.snow,
    onSurface: Color(0xFF1B1B1B),
    outline: Color(0xFF6B6B6B),
  );

  static const darkScheme = ColorScheme(
    brightness: Brightness.dark,
    primary: AppColors.moss,
    onPrimary: Color(0xFF10261C),
    secondary: AppColors.pine,
    onSecondary: AppColors.snow,
    error: Color(0xFFFB923C),
    onError: Color(0xFF3B1300),
    surface: AppColors.night,
    onSurface: Color(0xFFEDEDED),
    outline: Color(0xFF4A4A4A),
  );

  static const _text = TextTheme(
    headlineSmall: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
    titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
    bodyMedium: TextStyle(fontSize: 14),
    bodySmall: TextStyle(fontSize: 12, color: AppColors.granite),
  );

  static final light = ThemeData(colorScheme: lightScheme, textTheme: _text, useMaterial3: true);
  static final dark = ThemeData(colorScheme: darkScheme, textTheme: _text, useMaterial3: true);
}
