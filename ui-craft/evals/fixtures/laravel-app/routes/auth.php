<?php

use Illuminate\Support\Facades\Route;

Route::middleware('guest')->group(function () {
    Route::view('forgot-password', 'auth.forgot-password')->name('password.request');
});
