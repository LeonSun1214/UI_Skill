<div>
    <flux:heading size="xl">Settings</flux:heading>
    <form wire:submit="save" class="mt-6 space-y-4">
        <flux:input wire:model="name" label="Name" />
        <flux:button type="submit" variant="primary">Save</flux:button>
    </form>
</div>
