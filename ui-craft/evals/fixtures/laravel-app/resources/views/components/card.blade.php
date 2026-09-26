@props(['title', 'padded' => true])
<section {{ $attributes->class(['rounded-xl border border-zinc-200 dark:border-zinc-700', 'p-6' => $padded]) }}>
    <h2 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">{{ $title }}</h2>
    {{ $slot }}
</section>
