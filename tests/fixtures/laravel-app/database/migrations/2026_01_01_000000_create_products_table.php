<?php

class CreateProductsTable
{
    public function up(): void
    {
        // Schema::create('products', function ($table) {
        //     $table->id();
        //     $table->string('name');
        //     $table->decimal('price', 8, 2);
        //     $table->timestamps();
        // });
    }

    public function down(): void
    {
        // Schema::dropIfExists('products');
    }
}
