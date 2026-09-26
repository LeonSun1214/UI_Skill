<?php

use App\Http\Controllers\Admin\UsersController;
use App\Http\Controllers\ReportsController;
use App\Livewire\Settings;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::view('/', 'welcome')->name('home');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::view('dashboard', 'dashboard')->name('dashboard');
    Route::get('settings', Settings::class)->name('settings');
    Route::get('analytics', fn () => Inertia::render('Analytics'))->name('analytics');
});

// Reports: the overview is public, a report needs a session (the controller says which)
Route::get('reports', [ReportsController::class, 'index'])->name('reports.index');
Route::get('reports/{report}', [ReportsController::class, 'show'])->name('reports.show');

Route::prefix('admin')->group(function () {
    Route::get('users', [UsersController::class, 'index'])->name('admin.users');
});

Route::redirect('home', '/');

require __DIR__.'/auth.php';
