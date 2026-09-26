@extends('layouts.guest')

@section('content')
    <form method="POST" action="/login" class="space-y-4">
        @csrf
        <flux:input name="email" type="email" label="Email" />
        <flux:input name="password" type="password" label="Password" />
        <flux:button type="submit" variant="primary" class="w-full">Sign in</flux:button>
    </form>
@endsection
