@extends('layouts.guest')

@section('content')
    <form method="POST" action="/register" class="space-y-4">
        @csrf
        <flux:input name="name" label="Name" />
        <flux:input name="email" type="email" label="Email" />
        <flux:button type="submit" variant="primary" class="w-full">Create account</flux:button>
    </form>
@endsection
