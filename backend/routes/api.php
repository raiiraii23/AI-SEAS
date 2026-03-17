<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\SessionController;
use App\Http\Controllers\EngagementLogController;

/*
|--------------------------------------------------------------------------
| API Routes — /api/v1/*
|--------------------------------------------------------------------------
*/

Route::prefix('v1')->group(function () {

    // Health check
    Route::get('/health', fn () => response()->json(['status' => 'ok', 'service' => 'seas-backend']));

    // Auth
    Route::prefix('auth')->group(function () {
        Route::post('/register', [AuthController::class, 'register']);
        Route::post('/login', [AuthController::class, 'login']);
        Route::post('/logout', [AuthController::class, 'logout'])->middleware('auth:api');
        Route::get('/me', [AuthController::class, 'me'])->middleware('auth:api');
    });

    // Protected routes
    Route::middleware('auth:api')->group(function () {

        // Engagement sessions
        Route::apiResource('sessions', SessionController::class);

        // Engagement logs
        Route::get('sessions/{session}/logs', [EngagementLogController::class, 'index']);
        Route::post('sessions/{session}/logs', [EngagementLogController::class, 'store']);
        Route::get('sessions/{session}/summary', [EngagementLogController::class, 'summary']);
    });
});
