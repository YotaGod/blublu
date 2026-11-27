<?php

namespace App\Models;

class Product
{
    protected array $fillable = [
        'name',
        'price',
    ];

    public static function all(): array
    {
        return [
            ['id' => 1, 'name' => 'Mechanical Keyboard', 'price' => 129.99],
            ['id' => 2, 'name' => 'Wireless Mouse', 'price' => 59.99],
        ];
    }

    public static function find(int $id): ?array
    {
        $items = self::all();
        foreach ($items as $item) {
            if ($item['id'] === $id) {
                return $item;
            }
        }
        return null;
    }

    public static function create(array $attributes): array
    {
        return array_merge(['id' => 3], $attributes);
    }
}
