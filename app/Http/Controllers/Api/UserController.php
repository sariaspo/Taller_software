<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\BulkStoreUsersRequest;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        [$perPage, $page] = $this->paginationParameters($request);

        return response()->json(User::query()
            ->orderBy('id')
            ->paginate($perPage, ['*'], 'page', $page));
    }

    public function emails(Request $request): JsonResponse
    {
        [$perPage, $page] = $this->paginationParameters($request);

        return response()->json(User::query()
            ->orderBy('id')
            ->paginate($perPage, ['id', 'email'], 'page', $page));
    }

    public function overTwenty(Request $request): JsonResponse
    {
        [$perPage, $page] = $this->paginationParameters($request);
        $cutoff = Carbon::now()->subYears(20)->toDateString();

        $users = User::query()
            ->where('birth_date', '<=', $cutoff)
            ->orderBy('id')
            ->paginate($perPage, ['*'], 'page', $page);

        return response()->json($users);
    }

    private function paginationParameters(Request $request): array
    {
        $validated = $request->validate([
            'page' => ['sometimes', 'integer', 'min:1'],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:200'],
        ]);

        return [
            (int) ($validated['per_page'] ?? 50),
            (int) ($validated['page'] ?? 1),
        ];
    }

    public function bulkStore(BulkStoreUsersRequest $request): JsonResponse
    {
        $created = [];

        foreach ($request->validated()['users'] as $userData) {
            $created[] = User::create([
                'name' => $userData['name'],
                'email' => $userData['email'],
                'birth_date' => $userData['birth_date'],
                'password' => Hash::make($userData['password'] ?? 'password'),
            ]);
        }

        return response()->json([
            'message' => 'Se crearon 3 usuarios correctamente.',
            'users' => $created,
        ], 201);
    }
}
