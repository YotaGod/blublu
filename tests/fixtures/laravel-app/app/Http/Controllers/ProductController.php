<?php

namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class ProductController
{
    public function index(): JsonResponse
    {
        $products = Product::all();
        return response()->json(['data' => $products]);
    }

    public function show(int $id): JsonResponse
    {
        $product = Product::find($id);
        if (!$product) {
            return response()->json(['error' => 'Product not found'], 404);
        }
        return response()->json(['data' => $product]);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'price' => 'required|numeric|min:0',
        ]);

        $product = Product::create($validated);
        return response()->json(['data' => $product], 201);
    }
}
