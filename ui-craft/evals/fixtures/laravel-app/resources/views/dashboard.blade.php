<x-app-layout>
    <div class="grid gap-4 md:grid-cols-3">
        <x-stat label="Revenue" value="$48,210" />
        <x-stat label="Invoices" value="1,284" />
        <x-stat label="Overdue" value="37" />
    </div>
    <x-card title="Recent invoices" class="mt-6">
        <flux:table>
            <flux:table.columns><flux:table.column>Client</flux:table.column><flux:table.column>Amount</flux:table.column></flux:table.columns>
        </flux:table>
    </x-card>
</x-app-layout>
