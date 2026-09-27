import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Signed in or not: the router listens, so signing in moves past the redirect.
class AuthState extends ChangeNotifier {
  bool signedIn = false;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    signedIn = prefs.getBool('signed_in') ?? false;
  }

  Future<void> signIn() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('signed_in', true);
    signedIn = true;
    notifyListeners();
  }
}

final auth = AuthState();
