<?php

namespace App\Http\Controllers;

use App\Models\EngagementLog;
use App\Models\EngagementSession;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class EngagementLogController extends Controller
{
    public function index(EngagementSession $session): JsonResponse
    {
        $this->authorizeSession($session);

        $logs = $session->logs()->orderBy('logged_at')->get();
        return response()->json($logs);
    }

    public function store(Request $request, EngagementSession $session): JsonResponse
    {
        $this->authorizeSession($session);

        $data = $request->validate([
            'emotion'       => 'required|string|max:50',
            'confidence'    => 'required|numeric|min:0|max:1',
            'engagement'    => 'required|in:engaged,neutral,confused,disengaged,unknown',
            'all_scores'    => 'sometimes|array',
            'logged_at'     => 'sometimes|date',
        ]);

        $log = $session->logs()->create([
            'emotion'    => $data['emotion'],
            'confidence' => $data['confidence'],
            'engagement' => $data['engagement'],
            'all_scores' => $data['all_scores'] ?? [],
            'logged_at'  => $data['logged_at'] ?? now(),
        ]);

        return response()->json($log, 201);
    }

    public function summary(EngagementSession $session): JsonResponse
    {
        $this->authorizeSession($session);

        $logs = $session->logs()->get();
        $total = $logs->count();

        if ($total === 0) {
            return response()->json(['total_logs' => 0, 'distribution' => [], 'dominant_engagement' => null]);
        }

        $distribution = $logs->groupBy('engagement')->map(fn ($group) => [
            'count'      => $group->count(),
            'percentage' => round(($group->count() / $total) * 100, 2),
        ]);

        $dominant = $distribution->sortByDesc('count')->keys()->first();

        return response()->json([
            'total_logs'          => $total,
            'distribution'        => $distribution,
            'dominant_engagement' => $dominant,
        ]);
    }

    private function authorizeSession(EngagementSession $session): void
    {
        if ($session->user_id !== auth('api')->id()) {
            abort(403, 'Unauthorized.');
        }
    }
}
