@props(['label', 'value', 'trend' => null])
<div class="rounded-lg bg-zinc-50 p-4 dark:bg-zinc-800">
    <p class="text-xs text-zinc-500 dark:text-zinc-400">{{ $label }}</p>
    <p class="text-2xl font-semibold">{{ $value }}</p>
</div>
