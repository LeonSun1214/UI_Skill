@extends('layouts.guest')

@section('content')
    <h1 class="text-2xl font-semibold">Reports</h1>
    <ul class="mt-4 space-y-2">
        @foreach ($reports as $report)
            <li><x-card :title="$report->name" :padded="false" /></li>
        @endforeach
    </ul>
@endsection
