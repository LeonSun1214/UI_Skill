<!doctype html>
<html lang="en">
<head>@include('partials.head')</head>
<body class="min-h-screen bg-white dark:bg-zinc-900">
    <flux:header class="border-b border-zinc-200 dark:border-zinc-700">
        <flux:brand href="/" name="Ledger" />
        <flux:navbar>
            <flux:navbar.item href="/dashboard">Dashboard</flux:navbar.item>
            <flux:navbar.item href="/reports">Reports</flux:navbar.item>
        </flux:navbar>
    </flux:header>
    <flux:main>{{ $slot }}</flux:main>
</body>
</html>
