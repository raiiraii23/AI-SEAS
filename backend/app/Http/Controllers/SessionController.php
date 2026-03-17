<?php

namespace App\Http\Controllers;

use App\Models\EngagementSession;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class SessionController extends Controller
{
    public function index(): JsonResponse
    {
        $sessions = auth('api')->user()
            ->sessions()
            ->orderByDesc('created_at')
            ->paginate(15);

        return response()->json($sessions);
    }

    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'title'      => 'required|string|max:255',
            'subject'    => 'sometimes|string|max:255',
            'started_at' => 'sometimes|date',
        ]);

        $session = auth('api')->user()->sessions()->create([
            'title'      => $data['title'],
            'subject'    => $data['subject'] ?? null,
            'started_at' => $data['started_at'] ?? now(),
            'status'     => 'active',
        ]);

        return response()->json($session, 201);
    }

    public function show(EngagementSession $session): JsonResponse
    {
        $this->authorizeSession($session);
        return response()->json($session->load('logs'));
    }

    public function update(Request $request, EngagementSession $session): JsonResponse
    {
        $this->authorizeSession($session);

        $data = $request->validate([
            'status'   => 'sometimes|in:active,ended',
            'ended_at' => 'sometimes|date',
        ]);

        if (isset($data['status']) && $data['status'] === 'ended') {
            $data['ended_at'] = $data['ended_at'] ?? now();
        }

        $session->update($data);
        return response()->json($session);
    }

    public function destroy(EngagementSession $session): JsonResponse
    {
        $this->authorizeSession($session);
        $session->delete();
        return response()->json(['message' => 'Session deleted.']);
    }

    private function authorizeSession(EngagementSession $session): void
    {
        if ($session->user_id !== auth('api')->id()) {
            abort(403, 'Unauthorized.');
        }
    }
}
