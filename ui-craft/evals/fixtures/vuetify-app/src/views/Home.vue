<template>
  <v-container>
    <h1 class="text-h4 mb-4">Orders</h1>
    <v-row>
      <v-col v-for="k in ['Open', 'Late', 'Shipped']" :key="k" cols="12" md="4">
        <v-card :title="k" text="12 this week" />
      </v-col>
    </v-row>
    <v-btn color="primary" class="mt-4">New order</v-btn>
  </v-container>
</template>
