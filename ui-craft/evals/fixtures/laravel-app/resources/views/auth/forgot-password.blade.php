@extends('layouts.guest')

@section('content')
    <form method="POST" action="/forgot-password"><flux:input name="email" type="email" label="Email" /></form>
@endsection
