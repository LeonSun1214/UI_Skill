<?php

namespace App\Http\Controllers;

use Illuminate\Auth\Middleware\Authenticate;

class ReportsController extends Controller
{
    public function __construct()
    {
        $this->middleware(Authenticate::class, ['except' => ['index']]);
    }

    public function index()
    {
        return view('reports.index', ['reports' => []]);
    }

    public function show(string $report)
    {
        return view('reports.show', ['report' => $report]);
    }
}
