<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('engagement_logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('session_id')
                ->references('id')
                ->on('engagement_sessions')
                ->cascadeOnDelete();
            $table->string('emotion', 50);
            $table->float('confidence');
            $table->enum('engagement', ['engaged', 'neutral', 'confused', 'disengaged', 'unknown']);
            $table->json('all_scores')->nullable(); // jsonb when switching to PostgreSQL
            $table->timestamp('logged_at')->useCurrent();
            $table->timestamps();

            $table->index(['session_id', 'logged_at']);
            $table->index('engagement');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('engagement_logs');
    }
};
