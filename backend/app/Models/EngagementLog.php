<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class EngagementLog extends Model
{
    use HasFactory;

    protected $fillable = ['session_id', 'emotion', 'confidence', 'engagement', 'all_scores', 'logged_at'];

    protected $casts = [
        'all_scores' => 'array',
        'logged_at'  => 'datetime',
        'confidence' => 'float',
    ];

    public function session()
    {
        return $this->belongsTo(EngagementSession::class);
    }
}
